// server.js — tiny proxy that keeps your Claude API key off the browser.
// The React app posts to http://localhost:3001/v1/messages, this forwards
// the request to Anthropic with your key attached.

import express from "express";
import cors from "cors";
import "dotenv/config";

const app = express();
app.use(cors());
app.use(express.json());

app.post("/v1/messages", async (req, res) => {
  try {
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": process.env.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify(req.body),
    });
    const data = await r.json();
    res.status(r.status).json(data);
  } catch (e) {
    res.status(500).json({ error: String(e) });
  }
});

app.listen(3001, () => console.log("ConstructGuard proxy running on http://localhost:3001"));
