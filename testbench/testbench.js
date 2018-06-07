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
const executionTimeIndicator = document.getElementById('execution-time');
const compilationTimeIndicator = document.getElementById('compilation-time');

var output = '';
var lastTest = '';


const resetUI = () => {
  tigerBody.textContent = '';
  watBody.textContent = '';
  expectedBody.textContent = '';
  outputBody.textContent = '';
  document.getElementById('tiger-implemented').className = notrunIndicator;
  document.getElementById('wat-compiled').className = notrunIndicator;
  document.getElementById('wasm-generated').className = notrunIndicator;
  document.getElementById('test-passes').className = notrunIndicator;
  document.getElementById('execution-time').textContent = '';
  document.getElementById('compilation-time').textContent = '';
}

// importObject has WebAssembly.Memory object and helper functions
const importObject = {
  env: {
    memory: new WebAssembly.Memory({
      initial: 10,
      maximum: 100
    }),
    print: arg => {
      output += arg;
      outputBody.appendChild(document.createTextNode(arg));
    }
  }
};


const fetchSource = (test, filetype) => {
  return fetch('tests/' + test + '.' + filetype)
    .then(response => {
      if (response.ok) {
        return response;
      }
      throw test + '.' + filetype + ' not found';
    })
    .then(response => {
      return response.text();
    })
    .then(result => {
      return {
        success: true,
        result: result
      };
    })
    .catch(err => {
      return {
        success: false,
        result: err
      };
    });
};


const fetchTiger = async (test) => {
  tigerHeader.textContent = test + '.tig';
  var tiger = await fetchSource(test, 'tig');
  document.getElementById('tiger-implemented').className = successIndicator;
  tigerBody.textContent = tiger.result;
  return tiger.success;
};


const fetchWat = async (test) => {
  var tigerSuccess = await fetchTiger(test);
  watHeader.textContent = test + '.wat';
  if (tigerSuccess === true) {
    var wat = await fetchSource(test, 'wat');
    watBody.textContent = wat.result;
    if (/not found/g.exec(wat.result)) {
      document.getElementById('wat-compiled').className = failureIndicator;

      var error = await fetchSource(test, 'err');
      expectedBody.textContent = error.result;

      return false;
    } else {
      document.getElementById('wat-compiled').className = successIndicator;

      var compilationTimeRequest = await fetch('/comptime');
      var compilationTime = await compilationTimeRequest.text();
      document.getElementById('compilation-time').textContent = 'compilation in ' + compilationTime;

      return wat.success;
    }
  } else {
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
    var wasm = fetch('tests/' + test + '.wasm');
    document.getElementById('wasm-generated').className = successIndicator;
    WebAssembly.instantiateStreaming(wasm, importObject)
      .then(async wasmObject => {
        outputBody.textContent = 'actual:\n';
        output = '';

        var startExecution = performance.now();
        wasmObject.instance.exports.main();
        var executionTime = performance.now() - startExecution;
        executionTimeIndicator.textContent = 'execution in ' + executionTime.toFixed(2) + 'ms';

        var expected = await fetchExpected(test, 'out.bak');
        expectedBody.textContent = 'expected:\n' + expected;
        if (expected === output) {
          document.getElementById('test-passes').className = successIndicator;
        } else {
          document.getElementById('test-passes').className = failureIndicator;
        }
      })
      .catch(err => {
        document.getElementById('wasm-generated').className = failureIndicator;
        outputBody.textContent = err;
      });
  }
  lastTest = test; // save for run again button
};


function runTest(test) {
  resetUI();
  fetchWasm(test); // start fetching
}


// attach click handlers to test menu entries
var basicTests = ['int', 'add', 'subtract', 'multiply', 'divide', 'lt', 'gt', 'eq', 'ne', 'le', 'ge',
  'and', 'or', 'var', 'assign', 'seq', 'func', 'letvar', 'letfunc',
  'for', 'while', 'if', 'ifelse', 'ifelseInt'
];
var integrationTests = ['funcs', 'ifnested', 'letInt', 'letvars', 'letfuncs', 'letfunchain', 'letnested',
  'recursiveCount', 'recursiveSum', 'fibonacci', 'subprimes'
];
var errorTests = ['varNotDeclared', 'varNotDeclaredAssign', 'funcNotDeclared', 'funcMissingArgs', 'funcExcessiveArgs',
  'forReturnsValue', 'whileReturnsValue', 'ifelseTypeMismatch'
];


jQuery('#basic')
  .find('a')
  .each((index, test) => {
    jQuery(test)
      .on('click', () => {
        runTest(basicTests[index]);
      });
  });

jQuery('#integration')
  .find('a')
  .each((index, test) => {
    jQuery(test)
      .on('click', () => {
        runTest(integrationTests[index]);
      });
  });

jQuery('#errors')
  .find('a')
  .each((index, test) => {
    jQuery(test)
      .on('click', () => {
        runTest(errorTests[index]);
      });
  });


jQuery('#run-again')
  .on('click', () => {
    if (lastTest !== '') {
      runTest(lastTest);
    }
  });
