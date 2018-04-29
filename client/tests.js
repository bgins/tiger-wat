'use strict';

const tigerHeader = document.getElementById('tiger-header');
const tigerBody = document.getElementById('tiger-body');
const watHeader = document.getElementById('wat-header');
const watBody = document.getElementById('wat-body');
const outputBody = document.getElementById('output-body');

// WebAssembly.Memory object
var importObject = {
  env: {
    memory: new WebAssembly.Memory({
      initial: 10,
      maximum: 100
    })
  }
};

const fetchSource = (test, filetype) => {
  return fetch('tests/' + test + '.' + filetype)
    .then(response => {
      return response.text();
    });
};

function runTest(test) {
  fetchSource(test, 'tig')
    .then(tigerSource => {
      tigerHeader.textContent = test + '.tig';
      tigerBody.textContent = tigerSource;
    });

  fetchSource(test, 'wat')
    .then(watSource => {
      watHeader.textContent = test + '.wat';
      watBody.textContent = watSource;
    });

  WebAssembly.instantiateStreaming(fetch('tests/' + test + '.wasm'), importObject).then(wasmObject => {

    // console.log('1: ' + wasmObject.instance.exports.main());

    var outputString = '';
    switch (test) {
      case 'add':
        for (var i = 0, j = 10; i < 10; i++, j--) {
            var result = wasmObject.instance.exports.add(i, j);
            if (result === 10) { outputString += '✔'; }
            else { outputString += '✖'; }
            outputString += ' expect ' + i + ' + ' + j + ' to equal 10\n';
        }
        outputBody.textContent = outputString;
        break;
      case 'ints':
        for (var i = 0; i < 10; i++) {
          outputString += test + '\n';
        }
        outputBody.textContent = outputString;
        break;
      case 'limits':
        for (var i = 0; i < 10; i++) {
          outputString += test + '\n';
        }
        outputBody.textContent = outputString;
        break;
      default:
        console.log('no such test');
        break;
    }
  });
}

document.getElementById('ints').onclick = () => {
  runTest('ints');
}

document.getElementById('limits').onclick = () => {
  runTest('limits');
}

document.getElementById('add').onclick = () => {
  runTest('add');
}
