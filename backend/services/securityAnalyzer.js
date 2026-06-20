const CATEGORY_NAMES = [
  'Misconfigurations',
  'Identity Risks',
  'Vulnerabilities',
  'Resource Waste'
];

const SEVERITY_NAMES = ['Critical', 'High', 'Medium', 'Low'];

const SEVERITY_POINTS = {
  Critical: 12,
  High: 8,
  Medium: 4,
  Low: 2
};

const SEVERITY_RANK = {
  Critical: 4,
  High: 3,
  Medium: 2,
  Low: 1,
  Healthy: 0
};

const DANGEROUS_PORTS = new Set([22, 3389, 3306, 5432]);
const BROAD_PERMISSIONS = new Set(['*', 's3:*', 'iam:*', 'AdministratorAccess']);

function normalizeType(type = '') {
  return String(type).trim().toLowerCase();
}

function getResourceType(resource = {}) {
  return resource.type || resource.service || 'Unknown';
}

function hasResourceType(resource = {}, acceptedTypes) {
  const normalizedValues = [resource.type, resource.service]
    .filter(Boolean)
    .map(normalizeType);

  return acceptedTypes.some(type => normalizedValues.includes(normalizeType(type)));
}

function getOwner(resource = {}) {
  return resource.owner || (resource.tags && resource.tags.team) || 'unknown';
}

function getEnvironment(resource = {}) {
  return resource.environment || (resource.tags && resource.tags.env) || 'unknown';
}

function isSecurityGroup(resource) {
  return hasResourceType(resource, ['security group', 'securitygroup']);
}

function isIamResource(resource) {
  return hasResourceType(resource, ['iam role', 'iam', 'role', 'user']);
}

function isStorageResource(resource) {
  return hasResourceType(resource, ['object-storage', 'object storage', 's3', 's3 bucket', 'storage']);
}

function isDatabaseResource(resource) {
  return hasResourceType(resource, ['rds', 'database', 'rds database']);
}

function isEc2Resource(resource) {
  return hasResourceType(resource, ['vm', 'ec2', 'ec2 instance', 'virtual machine']);
}

function isContainerResource(resource) {
  return hasResourceType(resource, ['container']);
}

function isHostResource(resource) {
  return hasResourceType(resource, ['host']);
}

function isLoadBalancerResource(resource) {
  return hasResourceType(resource, ['load-balancer', 'load balancer', 'elb', 'alb', 'application load balancer']);
}

function isBlockStorageResource(resource) {
  return hasResourceType(resource, ['block-storage', 'block storage', 'ebs', 'volume', 'snapshot']);
}

function getDisplayResourceType(resource = {}) {
  const rawType = normalizeType(resource.type);

  if (rawType === 'public internet') return 'Public Internet';
  if (rawType === 'sensitive data') return 'Sensitive Data';
  if (isLoadBalancerResource(resource)) return 'Load Balancer';
  if (isEc2Resource(resource)) return 'EC2 Instance';
  if (isDatabaseResource(resource)) return 'RDS Database';
  if (isStorageResource(resource)) return 'S3 Bucket';
  if (isIamResource(resource)) return 'IAM Role';
  if (isBlockStorageResource(resource)) return 'Block Storage';
  if (hasResourceType(resource, ['serverless', 'lambda'])) return 'Lambda Function';
  if (hasResourceType(resource, ['network', 'elasticip', 'elastic ip'])) return 'Network Resource';
  if (isSecurityGroup(resource)) return 'Security Group';

  return getResourceType(resource);
}

function getConfig(resource) {
  if (!resource || typeof resource !== 'object') return {};

  const config = resource.config && typeof resource.config === 'object'
    ? resource.config
    : {};

  return {
    ...resource,
    ...config
  };
}

function getMetrics(resource) {
  if (!resource || typeof resource !== 'object') return {};

  const metrics = resource.metrics && typeof resource.metrics === 'object'
    ? resource.metrics
    : {};

  return {
    cpuUtilization: resource.cpuUtilizationPct,
    memoryUtilization: resource.memoryUtilizationPct,
    connectionCount: resource.connectionCount || resource.connections,
    networkInMb: resource.networkInMb,
    networkOutMb: resource.networkOutMb,
    requestCountDaily: resource.requestCountDaily,
    idleDays: resource.idleDays,
    lastAccessDays: resource.lastAccessDays,
    ...metrics
  };
}

function getPermissions(resource) {
  const config = getConfig(resource);
  const permissions = Array.isArray(config.permissions) ? [...config.permissions] : [];

  if (config.adminAccess === true) {
    permissions.push('AdministratorAccess');
  }

  return permissions;
}

function hasBroadPermission(resource) {
  return getPermissions(resource).some(permission => BROAD_PERMISSIONS.has(permission));
}

function hasS3BroadPermission(resource) {
  return getPermissions(resource).some(permission => (
    permission === '*' ||
    permission === 's3:*' ||
    permission === 'AdministratorAccess'
  ));
}

function getVulnerabilities(resource) {
  const configVulnerabilities = getConfig(resource).vulnerabilities;
  const directVulnerabilities = resource && resource.vulnerabilities;
  if (Array.isArray(configVulnerabilities)) return configVulnerabilities;
  if (Array.isArray(directVulnerabilities)) return directVulnerabilities;
  return [];
}

function getRulePort(rule = {}) {
  if (rule.port !== undefined) return Number(rule.port);
  if (rule.fromPort !== undefined && rule.toPort !== undefined && rule.fromPort === rule.toPort) {
    return Number(rule.fromPort);
  }
  return NaN;
}

function isPublicCidr(rule = {}) {
  return rule.source === '0.0.0.0/0' || rule.cidr === '0.0.0.0/0';
}

function hasPublicInternetAccess(resource) {
  const config = getConfig(resource);
  const openPortRules = Array.isArray(config.openPorts) ? config.openPorts : [];

  return config.publicAccess === true || openPortRules.some(isPublicCidr);
}

function isLikelySensitiveStorage(resource) {
  const text = `${resource.id || ''} ${resource.name || ''}`.toLowerCase();
  return (
    text.includes('blueprint') ||
    text.includes('customer') ||
    text.includes('backup') ||
    text.includes('data') ||
    getConfig(resource).containsSensitiveData === true
  );
}

function sameEnvironment(source, target) {
  const sourceEnv = getEnvironment(source);
  const targetEnv = getEnvironment(target);
  return sourceEnv !== 'unknown' && sourceEnv === targetEnv;
}

function sameTeam(source, target) {
  return getOwner(source) !== 'unknown' && getOwner(source) === getOwner(target);
}

function selectRelatedResources(source, candidates, limit = 3) {
  return candidates
    .map(candidate => {
      let score = 0;
      if (sameTeam(source, candidate)) score += 4;
      if (sameEnvironment(source, candidate)) score += 3;
      if (source.region && candidate.region && source.region === candidate.region) score += 2;
      return { candidate, score };
    })
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map(item => item.candidate);
}

function prepareCloudGraph(resources, relationships) {
  const preparedResources = resources.map(resource => {
    if (!isStorageResource(resource) || !isLikelySensitiveStorage(resource)) {
      return { ...resource };
    }

    return {
      ...resource,
      containsSensitiveData: true
    };
  });

  if (relationships.length > 0) {
    return {
      resources: preparedResources,
      relationships
    };
  }

  const inferredRelationships = [];
  const edgeKeys = new Set();

  function addEdge(source, target, type, label = type) {
    if (!source || !target || source === target) return;

    const edgeKey = `${source}:${target}:${type}`;
    if (edgeKeys.has(edgeKey)) return;

    edgeKeys.add(edgeKey);
    inferredRelationships.push({
      id: `rel-${String(inferredRelationships.length + 1).padStart(3, '0')}`,
      source,
      target,
      type,
      label
    });
  }

  const publicResources = preparedResources.filter(hasPublicInternetAccess);
  const loadBalancers = preparedResources.filter(isLoadBalancerResource);
  const computeResources = preparedResources.filter(isEc2Resource);
  const databases = preparedResources.filter(isDatabaseResource);
  const storageResources = preparedResources.filter(isStorageResource);
  const iamResources = preparedResources.filter(isIamResource);
  const needsPublicNode = publicResources.length > 0 || loadBalancers.length > 0;

  if (needsPublicNode) {
    preparedResources.unshift({
      id: 'internet-public',
      name: 'Public Internet',
      type: 'Public Internet',
      service: 'Network',
      owner: 'external',
      region: 'global',
      environment: 'public'
    });
  }

  loadBalancers.forEach(loadBalancer => {
    addEdge('internet-public', loadBalancer.id, 'exposed_to', 'exposed_to');

    selectRelatedResources(loadBalancer, computeResources, Math.min(Number(loadBalancer.targetCount) || 3, 3))
      .forEach(compute => addEdge(loadBalancer.id, compute.id, 'routes_to', 'routes_to'));
  });

  publicResources.forEach(resource => {
    addEdge('internet-public', resource.id, 'exposed_to', 'exposed_to');
  });

  computeResources.forEach(compute => {
    selectRelatedResources(compute, databases, 1)
      .forEach(database => addEdge(compute.id, database.id, 'connects_to', 'connects_to'));
  });

  iamResources
    .filter(resource => hasBroadPermission(resource) || hasS3BroadPermission(resource))
    .forEach(iamResource => {
      storageResources
        .filter(storage => sameEnvironment(iamResource, storage) || getEnvironment(storage) === 'prod')
        .forEach(storage => addEdge(iamResource.id, storage.id, 'can_access', 'can_access'));
    });

  storageResources
    .filter(isLikelySensitiveStorage)
    .forEach(storage => {
      const dataNodeId = `${storage.id}-sensitive-data`;
      preparedResources.push({
        id: dataNodeId,
        name: `${storage.name || storage.id} data`,
        type: 'Sensitive Data',
        service: 'Data',
        owner: getOwner(storage),
        region: storage.region || 'unknown',
        environment: getEnvironment(storage)
      });
      addEdge(storage.id, dataNodeId, 'contains_sensitive_data', 'contains_sensitive_data');
    });

  return {
    resources: preparedResources,
    relationships: inferredRelationships
  };
}

function createCounter(names) {
  return names.reduce((acc, name) => {
    acc[name] = 0;
    return acc;
  }, {});
}

function createFindingFactory() {
  let counter = 1;

  return function createFinding(input) {
    const resource = input.resource || {};
    const finding = {
      id: `finding-${String(counter).padStart(3, '0')}`,
      title: input.title,
      category: input.category,
      subCategory: input.subCategory,
      severity: input.severity,
      resourceId: input.resourceId || resource.id || 'unknown-resource',
      resourceName: input.resourceName || resource.name || 'Unknown resource',
      resourceType: input.resourceType || getDisplayResourceType(resource),
      owner: input.owner || getOwner(resource),
      region: input.region || resource.region || 'unknown',
      environment: input.environment || getEnvironment(resource),
      description: input.description,
      risk: input.risk,
      remediation: input.remediation,
      status: input.status || 'Open'
    };

    counter += 1;
    return finding;
  };
}

function detectMisconfigurations(resources, createFinding) {
  const findings = [];

  resources.forEach(resource => {
    const config = getConfig(resource);
    const openPortRules = Array.isArray(config.openPorts) ? config.openPorts : [];

    if (isSecurityGroup(resource)) {
      const inboundRules = Array.isArray(config.inboundRules) ? config.inboundRules : [];
      inboundRules.forEach(rule => {
        const port = getRulePort(rule);
        if (isPublicCidr(rule) && DANGEROUS_PORTS.has(port)) {
          findings.push(createFinding({
            resource,
            title: `Security group allows public access to port ${port}`,
            category: 'Misconfigurations',
            subCategory: 'Open Ports',
            severity: 'High',
            description: 'This security group allows inbound traffic from the public internet to a sensitive port.',
            risk: 'Attackers may attempt brute-force login, database attacks, or unauthorized remote access.',
            remediation: 'Restrict inbound access to trusted IP ranges only and avoid exposing sensitive ports to 0.0.0.0/0.'
          }));
        }
      });
    }

    openPortRules.forEach(rule => {
      const port = getRulePort(rule);
      if (isPublicCidr(rule) && DANGEROUS_PORTS.has(port)) {
        findings.push(createFinding({
          resource,
          title: `${resource.name || resource.id} exposes sensitive port ${port}`,
          category: 'Misconfigurations',
          subCategory: 'Open Ports',
          severity: 'High',
          description: 'This resource allows public internet traffic to a sensitive port.',
          risk: 'Public access to sensitive ports increases the chance of brute-force login, database probing, or unauthorized remote access.',
          remediation: 'Restrict this port to trusted private networks or approved IP ranges only.'
        }));
      }
    });

    if (isDatabaseResource(resource) && (config.encryptionEnabled === false || config.encryptionAtRest === false)) {
      findings.push(createFinding({
        resource,
        title: 'Database encryption is disabled',
        category: 'Misconfigurations',
        subCategory: 'Encryption Disabled',
        severity: 'High',
        description: 'This database does not have encryption at rest enabled.',
        risk: 'Sensitive data may be exposed if storage is accessed or compromised.',
        remediation: 'Enable encryption at rest for the database.'
      }));
    }

    if ((isStorageResource(resource) || isDatabaseResource(resource)) && config.publicAccess === true) {
      findings.push(createFinding({
        resource,
        title: isStorageResource(resource) ? 'S3 bucket allows public access' : 'Database is publicly accessible',
        category: 'Misconfigurations',
        subCategory: isStorageResource(resource) ? 'Public Storage Access' : 'Public Database Access',
        severity: 'High',
        description: isStorageResource(resource)
          ? 'This storage bucket is configured for public access.'
          : 'This database is configured with public access enabled.',
        risk: isStorageResource(resource)
          ? 'Publicly accessible storage can expose sensitive files or business data.'
          : 'Public databases are high-value targets and may expose business-critical data.',
        remediation: isStorageResource(resource)
          ? 'Disable public access and apply least privilege bucket policies.'
          : 'Disable public database access and keep database traffic private.'
      }));
    }

    if (config.loggingEnabled === false) {
      findings.push(createFinding({
        resource,
        title: 'Logging is disabled for this resource',
        category: 'Misconfigurations',
        subCategory: 'Logging Disabled',
        severity: 'Medium',
        description: 'This resource is not configured to emit security or operational logs.',
        risk: 'Security incidents may be harder to investigate without logs.',
        remediation: 'Enable logging and forward logs to a centralized monitoring platform.'
      }));
    }
  });

  return findings;
}

function detectIdentityRisks(resources, relationships, resourceById, createFinding) {
  const findings = [];

  resources.filter(isIamResource).forEach(resource => {
    const config = getConfig(resource);

    if (hasBroadPermission(resource)) {
      findings.push(createFinding({
        resource,
        title: 'IAM role has overly broad permissions',
        category: 'Identity Risks',
        subCategory: 'Over-Privileged IAM',
        severity: 'High',
        description: 'This IAM role includes wildcard or administrator-style permissions.',
        risk: 'Over-privileged roles increase the blast radius if credentials are compromised.',
        remediation: 'Apply least privilege access and replace wildcard permissions with specific actions.'
      }));
    }

    if (config.mfaEnabled === false || config.mfaRequired === false) {
      findings.push(createFinding({
        resource,
        title: 'MFA is disabled for IAM identity',
        category: 'Identity Risks',
        subCategory: 'MFA Disabled',
        severity: 'Medium',
        description: 'This IAM identity does not have MFA enabled.',
        risk: 'Accounts without MFA are more vulnerable to credential theft and unauthorized access.',
        remediation: 'Enable MFA for privileged identities and sensitive access paths.'
      }));
    }

    const accessKeyAgeDays = Number(config.accessKeyAgeDays);
    if (Number.isFinite(accessKeyAgeDays) && accessKeyAgeDays >= 180) {
      findings.push(createFinding({
        resource,
        title: 'IAM access key is older than 180 days',
        category: 'Identity Risks',
        subCategory: 'Stale Access Key',
        severity: config.adminAccess === true ? 'High' : 'Medium',
        description: 'This IAM identity uses a long-lived access key that has not been rotated recently.',
        risk: 'Old access keys increase the chance of credential leakage and make incident response harder.',
        remediation: 'Rotate the access key and move automation to short-lived credentials where possible.'
      }));
    }

    if (hasS3BroadPermission(resource)) {
      relationships
        .filter(rel => rel.source === resource.id && rel.type === 'can_access')
        .forEach(rel => {
          const target = resourceById.get(rel.target);
          if (target && isStorageResource(target) && getConfig(target).containsSensitiveData === true) {
            findings.push(createFinding({
              resource: target,
              resourceId: target.id,
              resourceName: target.name,
              resourceType: target.type,
              owner: resource.owner,
              region: target.region,
              title: 'IAM role can access sensitive S3 data',
              category: 'Identity Risks',
              subCategory: 'Sensitive Data Access',
              severity: 'High',
              description: `${resource.name || resource.id} can access a sensitive S3 bucket.`,
              risk: 'A compromised role could access or exfiltrate sensitive data.',
              remediation: 'Limit the IAM role to only required S3 actions and restrict access to sensitive buckets.'
            }));
          }
        });
    }
  });

  return findings;
}

function detectVulnerabilities(resources, createFinding) {
  const findings = [];

  resources
    .filter(resource => isContainerResource(resource) || isHostResource(resource) || isEc2Resource(resource))
    .forEach(resource => {
      getVulnerabilities(resource).forEach(vulnerability => {
        const severity = vulnerability.severity;
        if (severity !== 'Critical' && severity !== 'High') return;

        const cve = vulnerability.id || vulnerability.cve || 'unknown CVE';
        const subCategory = isContainerResource(resource)
          ? 'Container Vulnerability'
          : 'Host Vulnerability';

        findings.push(createFinding({
          resource,
          title: `${severity} vulnerability detected: ${cve}`,
          category: 'Vulnerabilities',
          subCategory,
          severity,
          description: `${resource.name || resource.id} has a ${severity.toLowerCase()} vulnerability in ${vulnerability.package || 'an installed package'}.`,
          risk: 'Critical vulnerabilities may be exploitable and could allow compromise of the workload or host.',
          remediation: 'Upgrade the affected package or rebuild the image using a patched base image.'
        }));
      });
    });

  return findings;
}

function detectResourceWaste(resources, createFinding) {
  const findings = [];

  resources.forEach(resource => {
    const metrics = getMetrics(resource);
    const config = getConfig(resource);
    const cpuUtilization = Number(metrics.cpuUtilization);
    const networkInMb = Number(metrics.networkInMb);
    const networkOutMb = Number(metrics.networkOutMb);
    const idleDays = Number(metrics.idleDays);

    if (
      isEc2Resource(resource) &&
      (
        (Number.isFinite(cpuUtilization) && cpuUtilization < 5) ||
        (Number.isFinite(idleDays) && idleDays >= 21)
      ) &&
      (!Number.isFinite(networkInMb) || networkInMb < 5) &&
      (!Number.isFinite(networkOutMb) || networkOutMb < 5)
    ) {
      findings.push(createFinding({
        resource,
        title: 'EC2 instance appears underutilized',
        category: 'Resource Waste',
        subCategory: 'Unused Resource',
        severity: 'Low',
        description: 'This EC2 instance has very low CPU and network activity.',
        risk: 'Unused or idle compute resources increase cost and may expand the attack surface unnecessarily.',
        remediation: 'Review whether the instance is still needed. Stop, resize, or terminate the resource if appropriate.'
      }));
    }

    const connectionCount = metrics.connectionCount !== undefined
      ? Number(metrics.connectionCount)
      : Number(metrics.connections);

    if (isDatabaseResource(resource) && Number.isFinite(connectionCount) && connectionCount < 3) {
      findings.push(createFinding({
        resource,
        title: 'Database appears underutilized',
        category: 'Resource Waste',
        subCategory: 'Underutilized Database',
        severity: 'Low',
        description: 'This database has very few active connections.',
        risk: 'Underused databases increase cost and may create unnecessary security management overhead.',
        remediation: 'Review usage patterns and consider downsizing, pausing, or consolidating the database.'
      }));
    }

    if (isBlockStorageResource(resource) && (config.attached === false || config.status === 'available')) {
      findings.push(createFinding({
        resource,
        title: 'Block storage volume appears orphaned',
        category: 'Resource Waste',
        subCategory: 'Orphaned Storage',
        severity: 'Low',
        description: 'This block storage resource is not attached to an active workload.',
        risk: 'Orphaned storage creates avoidable cost and unnecessary data retention exposure.',
        remediation: 'Confirm whether the volume is needed, snapshot it if required, and delete unused storage.'
      }));
    }

    const requestCountDaily = Number(metrics.requestCountDaily);
    if (isLoadBalancerResource(resource) && Number.isFinite(requestCountDaily) && requestCountDaily <= 10) {
      findings.push(createFinding({
        resource,
        title: 'Load balancer has almost no traffic',
        category: 'Resource Waste',
        subCategory: 'Unused Load Balancer',
        severity: 'Low',
        description: 'This load balancer receives very little traffic.',
        risk: 'Unused public entry points increase cost and keep unnecessary network exposure online.',
        remediation: 'Review whether this load balancer is still needed and decommission it if unused.'
      }));
    }

    const lastAccessDays = Number(metrics.lastAccessDays);
    if (isStorageResource(resource) && Number.isFinite(lastAccessDays) && lastAccessDays >= 180) {
      findings.push(createFinding({
        resource,
        title: 'Storage data has not been accessed recently',
        category: 'Resource Waste',
        subCategory: 'Cold Storage',
        severity: 'Low',
        description: 'This storage bucket contains data that has not been accessed for a long period.',
        risk: 'Rarely accessed data may be costing more than necessary in its current storage class.',
        remediation: 'Move archival data to a lower-cost storage class or apply a lifecycle policy.'
      }));
    }
  });

  return findings;
}

function detectHighRiskPaths(resources, relationships, createFinding) {
  const findings = [];
  const resourceById = new Map(resources.map(resource => [resource.id, resource]));
  const seenPaths = new Set();

  // Public Internet -> Database
  relationships
    .filter(rel => rel.type === 'exposed_to')
    .forEach(publicExposure => {
      const internet = resourceById.get(publicExposure.source);
      const database = resourceById.get(publicExposure.target);
      if (!internet || !database || !isDatabaseResource(database)) return;

      const pathKey = `internet-direct-db:${internet.id}:${database.id}`;
      if (seenPaths.has(pathKey)) return;
      seenPaths.add(pathKey);
      seenPaths.add(`direct-public-db:${database.id}`);

      findings.push(createFinding({
        resource: database,
        resourceId: database.id,
        resourceName: database.name || database.id,
        resourceType: getDisplayResourceType(database),
        title: 'Production database is directly exposed to the public internet',
        category: 'Misconfigurations',
        subCategory: 'Risky Attack Path',
        severity: 'Critical',
        description: 'A direct relationship exists from the public internet to a database resource.',
        risk: 'Direct public exposure makes the database a high-value target for scanning, credential attacks, and data compromise.',
        remediation: 'Remove public exposure and allow database access only from trusted private application resources.'
      }));
    });

  // Public Internet -> Load Balancer -> EC2 -> Database
  relationships
    .filter(rel => rel.type === 'exposed_to')
    .forEach(internetToLoadBalancer => {
      const internet = resourceById.get(internetToLoadBalancer.source);
      const loadBalancer = resourceById.get(internetToLoadBalancer.target);
      if (!internet || !loadBalancer) return;

      relationships
        .filter(rel => rel.source === loadBalancer.id && rel.type === 'routes_to')
        .forEach(loadBalancerToEc2 => {
          const ec2 = resourceById.get(loadBalancerToEc2.target);
          if (!ec2 || !isEc2Resource(ec2)) return;

          relationships
            .filter(rel => rel.source === ec2.id && rel.type === 'connects_to')
            .forEach(ec2ToDatabase => {
              const database = resourceById.get(ec2ToDatabase.target);
              if (!database || !isDatabaseResource(database)) return;
              if (seenPaths.has(`direct-public-db:${database.id}`)) return;

              const pathKey = `internet-db:${database.id}`;
              if (seenPaths.has(pathKey)) return;
              seenPaths.add(pathKey);

              findings.push(createFinding({
                resource: database,
                resourceId: database.id || ec2.id,
                resourceName: database.name || ec2.name,
                resourceType: database.type || ec2.type,
                title: 'Public internet path can reach production database',
                category: 'Misconfigurations',
                subCategory: 'Risky Attack Path',
                severity: 'Critical',
                description: 'A relationship path exists from the public internet through application infrastructure to a production database.',
                risk: 'An internet-facing entry point may provide an attack path toward the production database.',
                remediation: 'Restrict public exposure, harden the load balancer and EC2 instance, and limit database access to private trusted resources.'
              }));
            });
        });
    });

  // IAM Role -> S3 Bucket -> Sensitive Data
  resources.filter(isIamResource).forEach(iamRole => {
    if (!hasS3BroadPermission(iamRole)) return;

    relationships
      .filter(rel => rel.source === iamRole.id && rel.type === 'can_access')
      .forEach(roleToBucket => {
        const bucket = resourceById.get(roleToBucket.target);
        if (!bucket || !isStorageResource(bucket) || getConfig(bucket).containsSensitiveData !== true) return;

        relationships
          .filter(rel => rel.source === bucket.id && rel.type === 'contains_sensitive_data')
          .forEach(bucketToData => {
            const sensitiveData = resourceById.get(bucketToData.target);
            if (!sensitiveData) return;

            const pathKey = `iam-data:${iamRole.id}:${bucket.id}:${sensitiveData.id}`;
            if (seenPaths.has(pathKey)) return;
            seenPaths.add(pathKey);

            findings.push(createFinding({
              resource: sensitiveData,
              resourceId: sensitiveData.id,
              resourceName: sensitiveData.name,
              resourceType: sensitiveData.type,
              owner: iamRole.owner,
              region: sensitiveData.region,
              title: 'Over-privileged IAM role can reach sensitive data',
              category: 'Identity Risks',
              subCategory: 'Sensitive Data Attack Path',
              severity: 'Critical',
              description: `${iamRole.name || iamRole.id} can reach sensitive data through ${bucket.name || bucket.id}.`,
              risk: 'A compromised IAM role could directly access sensitive data.',
              remediation: 'Remove wildcard permissions and apply strict least-privilege access to sensitive data stores.'
            }));
          });
      });
  });

  return findings;
}

function calculateScoreBreakdown(findings) {
  const severityCounts = createCounter(SEVERITY_NAMES);
  findings.forEach(finding => {
    if (severityCounts[finding.severity] !== undefined) severityCounts[finding.severity] += 1;
  });

  const deductions = SEVERITY_NAMES.map(severity => {
    const count = severityCounts[severity];
    const pointsEach = SEVERITY_POINTS[severity];
    return {
      severity,
      count,
      pointsEach,
      totalDeduction: count * pointsEach
    };
  });

  const totalDeduction = deductions.reduce((sum, item) => sum + item.totalDeduction, 0);
  const finalScore = Math.max(0, 100 - totalDeduction);

  return {
    startingScore: 100,
    deductions,
    finalScore
  };
}

function calculateSecurityScore(findings) {
  return calculateScoreBreakdown(findings).finalScore;
}

function getHealthStatus(score) {
  if (score >= 80) return 'Healthy';
  if (score >= 60) return 'Needs Attention';
  return 'High Risk';
}

function getHighestSeverity(findings) {
  return findings.reduce((highest, finding) => {
    return SEVERITY_RANK[finding.severity] > SEVERITY_RANK[highest]
      ? finding.severity
      : highest;
  }, 'Healthy');
}

function buildSecuritySummary(findings) {
  const categoryBreakdown = createCounter(CATEGORY_NAMES);
  const severityBreakdown = createCounter(SEVERITY_NAMES);

  findings.forEach(finding => {
    if (categoryBreakdown[finding.category] !== undefined) categoryBreakdown[finding.category] += 1;
    if (severityBreakdown[finding.severity] !== undefined) severityBreakdown[finding.severity] += 1;
  });

  const scoreBreakdown = calculateScoreBreakdown(findings);
  const securityScore = calculateSecurityScore(findings);

  return {
    securityScore,
    healthStatus: getHealthStatus(securityScore),
    totalFindings: findings.length,
    criticalFindings: severityBreakdown.Critical,
    highFindings: severityBreakdown.High,
    mediumFindings: severityBreakdown.Medium,
    lowFindings: severityBreakdown.Low,
    categoryBreakdown,
    severityBreakdown,
    scoreBreakdown
  };
}

function buildDashboardData(findings) {
  const categoryCounts = createCounter(CATEGORY_NAMES);
  const severityCounts = createCounter(SEVERITY_NAMES);
  const findingsByResource = new Map();

  findings.forEach(finding => {
    categoryCounts[finding.category] += 1;
    severityCounts[finding.severity] += 1;

    if (!findingsByResource.has(finding.resourceId)) {
      findingsByResource.set(finding.resourceId, []);
    }
    findingsByResource.get(finding.resourceId).push(finding);
  });

  const topRiskyResources = Array.from(findingsByResource.entries())
    .map(([resourceId, resourceFindings]) => {
      const firstFinding = resourceFindings[0];
      return {
        resourceId,
        resourceName: firstFinding.resourceName,
        resourceType: firstFinding.resourceType,
        findingCount: resourceFindings.length,
        highestSeverity: getHighestSeverity(resourceFindings)
      };
    })
    .sort((a, b) => {
      const severityDiff = SEVERITY_RANK[b.highestSeverity] - SEVERITY_RANK[a.highestSeverity];
      if (severityDiff !== 0) return severityDiff;
      return b.findingCount - a.findingCount;
    })
    .slice(0, 5);

  return {
    findingsByCategory: CATEGORY_NAMES.map(name => ({ name, value: categoryCounts[name] })),
    findingsBySeverity: SEVERITY_NAMES.map(name => ({ name, value: severityCounts[name] })),
    topRiskyResources,
    totalFindings: findings.length,
    criticalFindings: severityCounts.Critical,
    highFindings: severityCounts.High
  };
}

function buildGraphData(resources, relationships, findings) {
  const findingsByResource = new Map();

  findings.forEach(finding => {
    if (!findingsByResource.has(finding.resourceId)) {
      findingsByResource.set(finding.resourceId, []);
    }
    findingsByResource.get(finding.resourceId).push(finding);
  });

  const nodes = resources.map(resource => {
    const resourceFindings = findingsByResource.get(resource.id) || [];
    return {
      id: resource.id,
      label: resource.name || resource.id,
      type: getDisplayResourceType(resource),
      riskLevel: getHighestSeverity(resourceFindings),
      findingCount: resourceFindings.length,
      owner: getOwner(resource),
      region: resource.region || 'unknown',
      environment: getEnvironment(resource)
    };
  });

  const edges = relationships.map((relationship, index) => ({
    id: relationship.id || `edge-${String(index + 1).padStart(3, '0')}`,
    source: relationship.source,
    target: relationship.target,
    label: relationship.label || relationship.type || 'related',
    type: relationship.type || 'related'
  }));

  return {
    nodes,
    edges
  };
}

function analyzeSecurityData(data = {}) {
  const rawResources = Array.isArray(data.resources) ? data.resources : [];
  const rawRelationships = Array.isArray(data.relationships) ? data.relationships : [];
  const preparedGraph = prepareCloudGraph(rawResources, rawRelationships);
  const resources = preparedGraph.resources;
  const relationships = preparedGraph.relationships;
  const resourceById = new Map(resources.map(resource => [resource.id, resource]));
  const createFinding = createFindingFactory();

  const findings = [
    ...detectMisconfigurations(resources, createFinding),
    ...detectIdentityRisks(resources, relationships, resourceById, createFinding),
    ...detectVulnerabilities(resources, createFinding),
    ...detectResourceWaste(resources, createFinding),
    ...detectHighRiskPaths(resources, relationships, createFinding)
  ];

  const securitySummary = buildSecuritySummary(findings);
  const dashboardData = buildDashboardData(findings);
  const graphData = buildGraphData(resources, relationships, findings);

  return {
    securitySummary,
    findings,
    dashboardData,
    graphData
  };
}

module.exports = {
  analyzeSecurityData
};
