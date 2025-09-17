// llm_vis – Entry #2: Histogram + Line (alt style / Dark2 palette / shapes)
// DIFFERENCES vs hand-tuned root: Dark2 palette, symbol shapes, gridlines, curveMonotoneX, different class names

const DATE_PARSE = d3.timeParse("%Y-%m-%d");
const DATA_ROOT = "../data/";

// shared dims
const M = { left: 50, right: 18, top: 20, bottom: 32 };
const W = 500 - M.left - M.right;
const H = 260 - M.top - M.bottom;

// formatters
const fmtInt = d3.format(",");
const fmtPct = d3.format(".0f");
const monthFmt = d3.timeFormat("%b");
const yTickFormatFor = (metric) => metric === "on_time_pct" ? (d) => fmtPct(d) + "%" : (d) => fmtInt(d);

// ColorBrewer Dark2 (distinct from Set1 in your main)
const dayTypeColor = d3.scaleOrdinal()
  .domain(["Weekday","Weekend","Holiday"])
  .range(["#1b9e77","#d95f02","#7570b3"]);

// Symbol shapes for day_type (distinctive vs main)
const dayTypeSymbol = d3.scaleOrdinal()
  .domain(["Weekday","Weekend","Holiday"])
  .range([d3.symbolCircle, d3.symbolSquare, d3.symbolTriangle]);

document.addEventListener("DOMContentLoaded", () => {
  d3.select("#dataset").on("change", changeData);
  d3.select("#metric").on("change", changeData);

  // scaffold SVGs
  ["Histogram-div","Linechart-div","StackedArea-div","Scatterplot-div"].forEach(id => {
    const svg = d3.select("#" + id).append("svg").attr("viewBox", "0 0 500 260");
    svg.append("g").attr("class", "plot").attr("transform", `translate(${M.left},${M.top})`);
    svg.append("g").attr("class", "x-axis").attr("transform", `translate(${M.left},${M.top + H})`);
    svg.append("g").attr("class", "y-axis").attr("transform", `translate(${M.left},${M.top})`);
    // gridline groups
    svg.append("g").attr("class", "grid-x").attr("transform", `translate(${M.left},${M.top + H})`);
    svg.append("g").attr("class", "grid-y").attr("transform", `translate(${M.left},${M.top})`);
    // legends
    svg.append("g").attr("class", "legend").attr("transform", `translate(${M.left + W - 120}, ${M.top + 10})`);
  });

  changeData();
});

function changeData() {
  const file = d3.select("#dataset").property("value");
  const metric = d3.select("#metric").property("value");

  d3.csv(DATA_ROOT + file).then(raw => {
    const rows = raw.map(d => ({
      date: DATE_PARSE(d.date),
      group: d.group,
      ridership: +d.ridership,
      on_time_pct: +d.on_time_pct,
      day_type: d.day_type
    })).filter(d => d.date);

    rows.sort((a, b) => a.date - b.date);

    updateHistogram(rows, metric);
    updateLineAlt(rows, metric); // alt-styled line
    // stacked & scatter will be added in Entries #3/#4
  }).catch(err => {
    console.error("Failed to load CSV:", err);
    alert("Error loading CSV. Check ../data/ and filenames.");
  });
}

/* ---------------- Histogram (same behavior, different styling OK) ---------------- */
function updateHistogram(rows, metric) {
  const svg = d3.select("#Histogram-div svg");
  const gPlot = svg.select(".plot");
  const gX = svg.select(".x-axis");
  const gY = svg.select(".y-axis");
  const gGridY = svg.select(".grid-y");

  const values = rows.map(d => d[metric]).filter(Number.isFinite);
  const x = d3.scaleLinear().domain(d3.extent(values)).nice().range([0, W]);
  const bins = d3.bin().domain(x.domain()).thresholds(24)(values);
  const y = d3.scaleLinear().domain([0, d3.max(bins, b => b.length) || 1]).nice().range([H, 0]);

  const t = svg.transition().duration(600).ease(d3.easeCubicInOut);

  const bars = gPlot.selectAll("rect.bar").data(bins, d => `${d.x0}-${d.x1}`);
  bars.join(
    enter => enter.append("rect")
      .attr("class", "bar")
      .attr("x", d => x(d.x0) + 1)
      .attr("width", d => Math.max(0, x(d.x1) - x(d.x0) - 1))
      .attr("y", H)
      .attr("height", 0)
      .attr("opacity", 0.95)
      .call(e => e.transition(t)
        .attr("y", d => y(d.length))
        .attr("height", d => H - y(d.length))),
    update => update
      .call(u => u.transition(t)
        .attr("x", d => x(d.x0) + 1)
        .attr("width", d => Math.max(0, x(d.x1) - x(d.x0) - 1))
        .attr("y", d => y(d.length))
        .attr("height", d => H - y(d.length))),
    exit => exit.call(xe => xe.transition(t).attr("opacity", 0).remove())
  );

  const xTickFmt = (metric === "on_time_pct") ? (d => d + "%") : fmtInt;
  gX.transition(t).call(d3.axisBottom(x).ticks(6).tickFormat(xTickFmt));
  gY.transition(t).call(d3.axisLeft(y).ticks(5));

  // horizontal gridlines
  gGridY.call(d3.axisLeft(y).ticks(5).tickSize(-W).tickFormat(""))
    .selectAll("line").attr("class","gridline");
}

/* ---------------- Line (ALT style): curveMonotoneX + shapes + Dark2 colors ---------------- */
function updateLineAlt(rows, metric) {
  const svg = d3.select("#Linechart-div svg");
  const gPlot = svg.select(".plot");
  const gX = svg.select(".x-axis");
  const gY = svg.select(".y-axis");
  const gGridY = svg.select(".grid-y");
  const legend = svg.select(".legend");

  const x = d3.scaleTime().domain(d3.extent(rows, d => d.date)).range([0, W]);
  const y = d3.scaleLinear().domain(d3.extent(rows, d => d[metric])).nice().range([H, 0]);

  const line = d3.line()
    .curve(d3.curveMonotoneX)
    .x(d => x(d.date))
    .y(d => y(d[metric]));

  const t = svg.transition().duration(650).ease(d3.easeCubicInOut);

  // gridlines + axes
  gGridY.call(d3.axisLeft(y).ticks(5).tickSize(-W).tickFormat("")).selectAll("line").attr("class","gridline");
  gX.transition(t).call(d3.axisBottom(x).ticks(d3.timeMonth.every(1)).tickFormat(monthFmt));
  gY.transition(t).call(d3.axisLeft(y).ticks(5).tickFormat(yTickFormatFor(metric)));

  // path
  gPlot.selectAll("path.path-line").data([rows]).join(
    enter => enter.append("path").attr("class","path-line").attr("d", line).attr("opacity",0)
      .call(e => e.transition(t).attr("opacity",1)),
    update => update.call(u => u.transition(t).attr("d", line))
  );

  // points as SYMBOL SHAPES (not circles)
  const sym = d3.symbol().size(52); // ~r=4-5 visual size
  const pts = gPlot.selectAll("path.pt-shape").data(rows, d => +d.date);
  pts.join(
    enter => enter.append("path")
      .attr("class","pt-shape")
      .attr("transform", d => `translate(${x(d.date)},${y(d[metric])})`)
      .attr("d", d => sym.type(dayTypeSymbol(d.day_type))())
      .attr("fill", d => dayTypeColor(d.day_type))
      .attr("opacity", 0)
      .call(e => e.transition().duration(300).ease(d3.easeCubicInOut).attr("opacity", 0.96)),
    update => update.call(u => u.transition(t)
      .attr("transform", d => `translate(${x(d.date)},${y(d[metric])})`)
      .attr("d", d => sym.type(dayTypeSymbol(d.day_type))())),
    exit => exit.call(xe => xe.transition().duration(250).attr("opacity",0).remove())
  );

  // legend (title + color chips + shape labels)
  if (legend.select("text.legend-title").empty()) {
    legend.append("text").attr("class","legend-title").attr("x",0).attr("y",-6)
      .style("font-size","12px").style("font-weight","600").text("Day type");
  }
  const cats = dayTypeColor.domain();
  const items = legend.selectAll("g.item").data(cats, d => d);
  const enter = items.enter().append("g").attr("class","item").attr("transform",(d,i)=>`translate(0,${i*18})`);
  enter.append("rect").attr("width", 12).attr("height", 12);
  enter.append("text").attr("x", 18).attr("y", 10);
  items.merge(enter).select("rect").attr("fill", d => dayTypeColor(d));
  items.merge(enter).select("text").text(d => d).style("font-size","12px");
  items.merge(enter).attr("transform",(d,i)=>`translate(0,${i*18})`);
}
