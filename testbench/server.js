'use strict';

const http = require('http');
const fs = require('fs');
const express = require('express');
var shell = require('shelljs');

const server = express();
const testPath = '../tests/';

var compilationTime = Infinity;

server.get('/comptime', (req, res) => {
  res.status(200);
  res.set({
    'Content-Type': 'text/plain'
  });
  res.send(compilationTime);
  compilationTime = Infinity;
});

server.get('/tests/:file', (req, res) => {
  if (/wat$/.exec(req.params.file)) {
    var tigerSource = req.params.file.slice(0, -4) + '.tig';
    shell.cd('..');
    shell.rm('tests/' + req.params.file);
    console.log('\n//~ ' + tigerSource + ' ~//');
    console.log('* Compiling wat *');
    shell.exec('python3 compiler.py ' + tigerSource, (code, stdout, stderr) => {
      compilationTime = stdout.split('\n').pop();
      console.log('\nExit code: ' + code);
      console.log('Program stderr: ' + stderr);
      shell.cd('-');
      res.sendFile(req.params.file, {
        'root': testPath
      });
    });
  } else if (/wasm$/.exec(req.params.file)) {
    var watSource = req.params.file.slice(0, -5) + '.wat';
    shell.cd(testPath);
    shell.rm(req.params.file);
    console.log('\n* Generating wasm *');
    shell.exec('wasm -d ' + watSource + ' -o ' + req.params.file, (code, stdout, stderr) => {
      fs.readFile(testPath + req.params.file, (err, data) => {
        console.log(stdout);
        console.log('Exit code: ' + code);
        console.log('Program stderr: ' + stderr);
        if (err === null) {
          res.set({
            'Content-Type': 'application/wasm'
          });
          res.send(new Buffer(data));
        } else {
          res.status(404).send('not found');
        }
      });
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
