'use strict';

const tigerHeader = document.getElementById('tiger-header');
const tigerBody = document.getElementById('tiger-body');
const watHeader = document.getElementById('wat-header');
const watBody = document.getElementById('wat-body');
const outputBody = document.getElementById('output-body');
const expectedBody = document.getElementById('expected-body');

// indicators
const notrunIndicator = 'fa fa-circle-thin fa-fw';
const successIndicator = 'fa fa-check text-success fa-fw';
const failureIndicator = 'fa fa-times text-danger fa-fw';

var outputString = '';
var lastTest = '';

const resetUI = () => {
  tigerBody.textContent = '';
  watBody.textContent = '';
  expectedBody.textContent = '';
  outputBody.textContent = '';
}

// imports has WebAssembly.Memory object and helper functions
const importObject = {
  env: {
    memory: new WebAssembly.Memory({
      initial: 10,
      maximum: 100
    }),
    // print_int: arg => outputString += arg + '\n'
    print: arg => outputString += arg + '\n'
  }
};


const fetchSource = (test, filetype, indicator) => {
  return fetch('tests/' + test + '.' + filetype)
    .then(response => {
      if (response.ok) {
        return response;
      }
      throw test + '.' + filetype + ' not found';
    })
    .then(response => {
      if (indicator !== undefined) {
        document.getElementById(indicator).className = successIndicator;
      }
      return response.text();
    })
    .then(result => {
      return {
        success: true,
        result: result
      };
    })
    .catch(err => {
      if (indicator !== undefined) {
        document.getElementById(indicator).className = failureIndicator;
      }
      return {
        success: false,
        result: err
      };
    });
};

const fetchTiger = async (test) => {
  tigerHeader.textContent = test + '.tig';
  var tiger = await fetchSource(test, 'tig', 'test-implemented');
  tigerBody.textContent = tiger.result;
  return tiger.success;
};

const fetchWat = async (test) => {
  var tigerSuccess = await fetchTiger(test);
  watHeader.textContent = test + '.wat';
  if (tigerSuccess === true) {
    var wat = await fetchSource(test, 'wat', 'test-generated');
    watBody.textContent = wat.result;
    return wat.success;
  } else {
    document.getElementById('test-generated').className = notrunIndicator;
    return false;
  }
};

const fetchExpected = async (test) => {
  var expected = await fetchSource(test, 'out.bak');
  return expected.result;
};

const fetchWasm = async (test) => {
  var watSuccess = await fetchWat(test);
  if (watSuccess === true) {
    WebAssembly.instantiateStreaming(fetch('tests/' + test + '.wasm'), importObject)
      .then(async wasmObject => {
        document.getElementById('test-validated').className = successIndicator;
        wasmObject.instance.exports.main();
        outputBody.textContent = 'actual:\n' + outputString;
        var expected = await fetchExpected(test, 'out.bak');
        expectedBody.textContent = 'expected:\n' + expected;
        if (expected === outputString) {
          document.getElementById('test-passes').className = successIndicator;
        } else {
          document.getElementById('test-passes').className = failureIndicator;
        }
        outputString = '';
      })
      .catch(err => {
        document.getElementById('test-validated').className = failureIndicator;
        document.getElementById('test-passes').className = notrunIndicator;
        outputBody.textContent = err;
      });
  } else {
    document.getElementById('test-validated').className = notrunIndicator;
    document.getElementById('test-passes').className = notrunIndicator;
  }
  lastTest = test; // save for run again button
};


function runTest(test) {
  resetUI();
  fetchWasm(test); // start fetching
}


// attach click handlers to test menu entries
var tests = ['int', 'add', 'subtract', 'multiply', 'divide', 'lt', 'gt', 'eq', 'ne', 'le', 'ge',
  'and', 'or', 'locals', 'assign', 'seq', 'funcdec', 'funcs', 'letvar', 'letfuncs', 'letfunchain'
];

jQuery('#test-selection')
  .find('a')
  .each((index, test) => {
    jQuery(test)
      .on('click', () => {
        runTest(tests[index]);
      });
  });

jQuery('#run-again')
  .on('click', () => {
    if (lastTest !== '') {
      runTest(lastTest);
    }
  });
