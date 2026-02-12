import express from "express";
import cors from "cors";
import { spawn } from "child_process";

const app = express();
app.use(cors());
app.use(express.json());

// start python process
let pythonProcess = null;

app.get("/start-detection", (req, res) => {
  if (pythonProcess) {
    return res.json({ message: "detection already running" });
  }

  pythonProcess = spawn("python", ["../detection/main.py"]);

  pythonProcess.stdout.on("data", (data) => {
    console.log(`python: ${data}`);
  });

  pythonProcess.stderr.on("data", (data) => {
    console.error(`python error: ${data}`);
  });

  pythonProcess.on("close", (code) => {
    console.log(`python process exited with code ${code}`);
    pythonProcess = null;
  });

  res.json({ message: "started detection" });
});

app.get("/stop-detection", (req, res) => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
    res.json({ message: "stopped detection" });
  } else {
    res.json({ message: "no detection running" });
  }
});

const PORT = 5000;
app.listen(PORT, () => console.log(`server running on port ${PORT}`));
