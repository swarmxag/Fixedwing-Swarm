const express = require('express');
const http = require('http');
const GStreamerPipeline = require('gst-node-bindings');

const app = express();
const server = http.createServer(app);

const pipelineString =
  'rtspsrc location=rtsp://192.168.0.119:554/main latency=0 ! queue ! application/x-rtp ! rtph264depay ! avdec_h264 ! videoconvert ! jpegenc ! appsink name=sink';

const pipeline = new GStreamerPipeline();
let latestJPEG = null;

pipeline.onFrame((jpegBuffer) => {
  latestJPEG = jpegBuffer;
});

// MJPEG stream endpoint
app.get('/stream', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'multipart/x-mixed-replace; boundary=frame',
    'Cache-Control': 'no-cache',
    Connection: 'close',
    Pragma: 'no-cache',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers':
      'Origin, X-Requested-With, Content-Type, Accept',
  });

  const sendFrame = () => {
    if (latestJPEG) {
      res.write(
        `--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ${latestJPEG.length}\r\n\r\n`
      );
      res.write(latestJPEG);
      res.write('\r\n');
    }
  };

  const interval = setInterval(sendFrame, 1000 / 15); // 15 FPS

  req.on('close', () => {
    clearInterval(interval);
    console.log('Client disconnected from stream');
  });

  req.on('error', (error) => {
    console.error('Stream request error:', error);
  });
});

const createPipeline = () => {
  pipeline.setPipeline(pipelineString);
  server.listen(9000, () => {
    console.log('Express server running on port 9000');
  });
  pipeline.start();
  return 'Started';
};

module.exports = createPipeline;
