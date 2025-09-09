// Constants for the charts, that would be useful.
const CHART_WIDTH = 500;
const CHART_HEIGHT = 250;
const MARGIN = { left: 50, bottom: 20, top: 20, right: 20 };
const ANIMATION_DUATION = 300;

setup();

function setup () {

  // Fill in some d3 setting up here if you need
  // for example, svg for each chart, g for axis and shapes

  changeData();
}

/**
 * Render the visualizations
 * @param data
 */
function update (data) {

  // ****** TODO ******

}

/**
 * Update the bar chart
 */

function updateHistogramChart () {

  // ****** TODO ******
}

/**
 * Update the line chart
 */
function updateLineChart () {

  // ****** TODO ******
}

/**
 * Update the area chart 
 */
function updateStackedAreaChart () {

  // ****** TODO ******
}

/**
 * update the scatter plot.
 */

function updateScatterPlot () {

  // ****** TODO ******
}


/**
 * Update the data according to document settings
 */
function changeData () {
  //  Load the file indicated by the select menu
  const dataFile = d3.select('#dataset').property('value');

  d3.csv(`data/${dataFile}.csv`)
    .then(dataOutput => {
      /**
       * D3 loads all CSV data as strings. While Javascript is pretty smart
       * about interpreting strings as numbers when you do things like
       * multiplication, it will still treat them as strings where it makes
       * sense (e.g. adding strings will concatenate them, not add the values
       * together, or comparing strings will do string comparison, not numeric
       * comparison).
       **/

      const dataResult = dataOutput.map((d) => ({
        attr1: parseFloat(d.attr1),
        attr2: parseFloat(d.attr2),
        attr3: d.attr3,
        date: d3.timeFormat("%m/%d")(d3.timeParse("%d-%b")(d.date))
      }));
      update(dataResult);
    }).catch(e => {
      console.log(e);
      alert('Error!');
    });
}
