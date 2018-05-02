'use strict';

const tigerHeader = document.getElementById('tiger-header');
const tigerBody = document.getElementById('tiger-body');
const watHeader = document.getElementById('wat-header');
const watBody = document.getElementById('wat-body');
const outputBody = document.getElementById('output-body');

var outputString = '';

// imports has WebAssembly.Memory object and helper functions
var importObject = {
  env: {
    memory: new WebAssembly.Memory({
      initial: 10,
      maximum: 100
    }),
    print_int: arg => outputString += arg + '\n'
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

  // fetch and instantiate wasm then run test
  WebAssembly.instantiateStreaming(fetch('tests/' + test + '.wasm'), importObject).then(wasmObject => {
    wasmObject.instance.exports.main();
    outputBody.textContent = outputString;
    outputString = '';
  });
}


// attach click handlers to test menu entries
var tests = ['ints', 'limits', 'add', 'subtract', 'multiply', 'divide'];

jQuery('#test-selection')
  .children()
  .children()
  .children()
  .each((index, test) => {
    jQuery(test)
      .on('click', () => {
        runTest(tests[index]);
      });
  });
