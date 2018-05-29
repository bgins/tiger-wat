'use strict';

const http = require('http');
const fs = require('fs');
const express = require('express');

const server = express();
const testPath = '../tests/';
// const testPath = '../handcoded/';

server.get('/tests/:file', function(req, res) {
  if (/wasm$/.exec(req.params.file)) {
    fs.readFile(testPath + req.params.file, (err, data) => {
      if (err === null) {
        res.set({
          'Content-Type': 'application/wasm'
        });
        res.send(new Buffer(data));
      } else {
        res.status(404).send('not found');
      }
    });
  } else {
    res.sendFile(req.params.file, {
      'root': testPath
    });
  }
});

server.use('/', express.static('./'));

console.log('server listening on port 8080');
server.listen(8080);
