import fs from "fs";
import express from "express";
import cors from "cors";
import { spawn } from "child_process";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const app = express();
app.use(cors());
app.use(express.json());

const PORT = 5000;

// path setup
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const audioLog = join(__dirname, "../audio/audio_log.json");

// only letters/numbers we care about
const INTERESTING_CHARS = ["a", "b", "c", "d", "1", "2", "3", "4"];

// ------------------------------
//  AUDIO PROCESS (runs always)
// ------------------------------
const audioProcess = spawn("python", ["../audio/audio.py"]);

audioProcess.stdout.on("data", (data) => {
  const str = data.toString().trim();
  try {
    const jsonData = JSON.parse(str);

    const hasCheating = jsonData.cheating_detected === true;
    const transcription = (jsonData.transcription || "").toLowerCase();
    const hasInteresting = INTERESTING_CHARS.some((c) =>
      transcription.includes(c)
    );

    if (hasCheating || hasInteresting) {
      console.log("audio event (logged):", jsonData);
      fs.appendFileSync(audioLog, JSON.stringify(jsonData) + "\n");
    }
  } catch (e) {
    console.error("failed to parse audio json:", str);
  }
});

audioProcess.stderr.on("data", (data) => {
  console.error("audio process error:", data.toString());
});

audioProcess.on("close", (code) => {
  console.log(`audio process exited with code ${code}`);
});

// ------------------------------
//  VIDEO PROCESS CONTROL (opencv)
// ------------------------------
let videoProcess = null;

app.get("/start-detection", (req, res) => {
  if (videoProcess) {
    return res.json({ message: "detection already running" });
  }

  videoProcess = spawn("python", ["../detection/main.py"]);

  videoProcess.stdout.on("data", (data) => {
    console.log(`python(video): ${data.toString().trim()}`);
  });

  videoProcess.stderr.on("data", (data) => {
    console.error(`python(video) error: ${data.toString()}`);
  });

  videoProcess.on("close", (code) => {
    console.log(`video detection exited with code ${code}`);
    videoProcess = null;
  });

  res.json({ message: "started detection" });
});

app.get("/stop-detection", (req, res) => {
  if (videoProcess) {
    videoProcess.kill();
    videoProcess = null;
    res.json({ message: "stopped detection" });
  } else {
    res.json({ message: "no detection running" });
  }
});

// ------------------------------
//  ROOT ENDPOINT
// ------------------------------
app.get("/", (req, res) => {
  res.send("audio + video detection server running...");
});

// ------------------------------
//  START SERVER
// ------------------------------
app.listen(PORT, () =>
  console.log(`server running on port ${PORT} (audio + video active)`)
);
