// ===== Config =====
const WIDTH = 520, HEIGHT = 300;
const M = { top: 26, right: 18, bottom: 36, left: 54 };
const DUR = 600; // <= 700ms subtle transitions

// Schema fields
const F_DATE = "date";
const F_GROUP = "group";
const F_Q1 = "ridership";
const F_Q2 = "on_time_pct";
const F_CAT = "day_type";

// Formatting & helpers
const parseDate = d3.timeParse("%Y-%m-%d");
const fmtInt = d3.format(",");
const fmtPct = d3.format(".0f");
const monthFmt = d3.timeFormat("%b");

const metricNames = {
  [F_Q1]: "Ridership (passengers/day)",
  [F_Q2]: "On-time performance (%)"
};

// ColorBrewer Set1 (3-class, colorblind-safe)
const dayTypeColor = d3.scaleOrdinal()
  .domain(["Weekday","Weekend","Holiday"])
  .range(["#e41a1c","#377eb8","#4daf4a"]);

// State
const state = {
  rows: [],
  metric: F_Q1,
  file: "route_a.csv"
};

// ==== Boot ====
document.addEventListener("DOMContentLoaded", () => {
  // controls
  d3.select("#dataset").on("change", () => {
    state.file = d3.select("#dataset").property("value");
    loadAndRender();
  });
  d3.select("#metric").on("change", () => {
    state.metric = d3.select("#metric").property("value");
    renderAll();
  });

  // build SVG scaffolds
  buildScaffold("#histogram", "hist");
  buildScaffold("#line", "line");
  buildScaffold("#stacked", "stack");
  buildScaffold("#scatter", "scatter");

  loadAndRender();
});

// store refs on container nodes
function buildScaffold(sel, key){
  const svg = d3.select(sel).append("svg")
    .attr("viewBox", `0 0 ${WIDTH} ${HEIGHT}`);

  const w = WIDTH - M.left - M.right;
  const h = HEIGHT - M.top - M.bottom;

  const plot = svg.append("g").attr("class","plot")
    .attr("transform", `translate(${M.left},${M.top})`);
  const xAxisG = svg.append("g").attr("class","x-axis")
    .attr("transform", `translate(${M.left},${M.top+h})`);
  const yAxisG = svg.append("g").attr("class","y-axis")
    .attr("transform", `translate(${M.left},${M.top})`);

  const xLabel = svg.append("text").attr("class","x-label")
    .attr("text-anchor","middle")
    .attr("x", M.left + w/2).attr("y", HEIGHT-6).text("");
  const yLabel = svg.append("text").attr("class","y-label")
    .attr("text-anchor","middle")
    .attr("transform", `translate(14, ${M.top + h/2}) rotate(-90)`).text("");

  const legend = svg.append("g").attr("class","legend")
    .attr("transform", `translate(${WIDTH - M.right - 124}, ${M.top + 8})`);

  // stash
  svg.node().__ref = { key, svg, plot, xAxisG, yAxisG, xLabel, yLabel, legend, w, h };
}

function getRef(sel){
  return d3.select(sel + " svg").node().__ref;
}

// ==== Data load ====
function loadAndRender(){
  const path = `data/${state.file}`;
  d3.csv(path).then(raw => {
    const rows = raw.map(d => ({
      date: parseDate(d[F_DATE]),
      group: d[F_GROUP],
      ridership: +d[F_Q1],
      on_time_pct: +d[F_Q2],
      day_type: d[F_CAT]
    })).filter(d => d.date && isFinite(d.ridership) && isFinite(d.on_time_pct));
    rows.sort((a,b) => a.date - b.date);
    state.rows = rows;
    renderAll();
  }).catch(err => {
    console.error("CSV load error:", err);
    alert("Error loading CSV. Check filename and schema.");
  });
}

function renderAll(){
  if(!state.rows.length) return;
  renderHistogram();
  renderLine();
  renderStacked();
  renderScatter();
}

// ==== Histogram ====
function renderHistogram(){
  const {plot, xAxisG, yAxisG, xLabel, yLabel, w, h} = getRef("#histogram");
  const metric = state.metric;
  const vals = state.rows.map(d => d[metric]);

  const x = d3.scaleLinear().domain(d3.extent(vals)).nice().range([0,w]);
  const bins = d3.bin().domain(x.domain()).thresholds(24)(vals);
  const y = d3.scaleLinear().domain([0, d3.max(bins, d => d.length) || 1]).nice().range([h,0]);

  const bars = plot.selectAll("rect.bar").data(bins, d => `${d.x0}-${d.x1}`);

  bars.join(
    enter => enter.append("rect")
      .attr("class","bar")
      .attr("x", d => x(d.x0)+1)
      .attr("width", d => Math.max(0, x(d.x1)-x(d.x0)-1))
      .attr("y", h).attr("height", 0).attr("opacity", .95)
      .transition().duration(DUR).ease(d3.easeCubicInOut)
        .attr("y", d => y(d.length))
        .attr("height", d => h - y(d.length)),
    update => update.transition().duration(DUR).ease(d3.easeCubicInOut)
        .attr("x", d => x(d.x0)+1)
        .attr("width", d => Math.max(0, x(d.x1)-x(d.x0)-1))
        .attr("y", d => y(d.length))
        .attr("height", d => h - y(d.length)),
    exit => exit.transition().duration(300).attr("opacity",0).remove()
  );

  xAxisG.transition().duration(DUR).ease(d3.easeCubicInOut)
    .call(d3.axisBottom(x).ticks(6)
      .tickFormat(metric === F_Q2 ? d => fmtPct(d)+"%" : fmtInt(d)));
  yAxisG.transition().duration(DUR).ease(d3.easeCubicInOut)
    .call(d3.axisLeft(y).ticks(5).tickFormat(fmtInt));

  xLabel.text(metricNames[metric] || metric);
  yLabel.text("Count");
}

// ==== Line ====
function renderLine(){
  const {plot, xAxisG, yAxisG, xLabel, yLabel, legend, w, h} = getRef("#line");
  const metric = state.metric;

  const x = d3.scaleTime().domain(d3.extent(state.rows, d => d.date)).range([0,w]);
  const y = d3.scaleLinear().domain(d3.extent(state.rows, d => d[metric])).nice().range([h,0]);
  const line = d3.line().x(d => x(d.date)).y(d => y(d[metric]));

  // path
  const path = plot.selectAll("path.line").data([state.rows]);
  path.join(
    enter => enter.append("path").attr("class","line")
      .attr("d", line).attr("opacity",0)
      .transition().duration(DUR).ease(d3.easeCubicInOut).attr("opacity",1),
    update => update.transition().duration(DUR).ease(d3.easeCubicInOut).attr("d", line)
  );

  // points colored by day_type
  const pts = plot.selectAll("circle.pt").data(state.rows, d => +d.date);
  pts.join(
    enter => enter.append("circle").attr("class","pt")
      .attr("r", 4).attr("stroke","#fff").attr("stroke-width",1.2)
      .attr("cx", d => x(d.date)).attr("cy", d => y(d[metric]))
      .attr("fill", d => dayTypeColor(d.day_type)).attr("opacity",0)
      .transition().duration(300).ease(d3.easeCubicInOut).attr("opacity",0.95),
    update => update.transition().duration(DUR).ease(d3.easeCubicInOut)
      .attr("cx", d => x(d.date)).attr("cy", d => y(d[metric])),
    exit => exit.transition().duration(250).attr("opacity",0).remove()
  );

  // axes
  xAxisG.transition().duration(DUR).ease(d3.easeCubicInOut)
    .call(d3.axisBottom(x).ticks(d3.timeMonth.every(1)).tickFormat(monthFmt));
  yAxisG.transition().duration(DUR).ease(d3.easeCubicInOut)
    .call(d3.axisLeft(y).ticks(5)
      .tickFormat(metric === F_Q2 ? d => fmtPct(d)+"%" : fmtInt(d)));

  xLabel.text("Date");
  yLabel.text(metricNames[metric] || metric);

  // legend (day type)
  if (legend.select(".legend-title").empty()){
    legend.append("text").attr("class","legend-title").attr("x",0).attr("y",-6).text("Day type");
  }
  const cats = dayTypeColor.domain();
  const items = legend.selectAll("g.item").data(cats, d => d);
  const enter = items.enter().append("g").attr("class","item");
  enter.append("rect").attr("width",12).attr("height",12);
  enter.append("text").attr("x",18).attr("y",10);
  items.merge(enter)
    .attr("transform",(d,i)=>`translate(0, ${i*18})`)
    .select("rect").attr("fill", d => dayTypeColor(d));
  items.merge(enter)
    .select("text").text(d=>d);
}

// ==== Stacked Area ====
function renderStacked(){
  const {plot, xAxisG, yAxisG, xLabel, yLabel, legend, w, h} = getRef("#stacked");

  const table = state.rows.map(d => ({date: d.date, ridership: d.ridership, on_time_pct: d.on_time_pct}));
  const keys = [F_Q1, F_Q2];

  const x = d3.scaleTime().domain(d3.extent(table, d=>d.date)).range([0,w]);
  const stack = d3.stack().keys(keys)(table);
  const y = d3.scaleLinear().domain([0, d3.max(stack[stack.length-1], d => d[1]) || 1]).nice().range([h,0]);

  const area = d3.area().x(d=>x(d.data.date)).y0(d=>y(d[0])).y1(d=>y(d[1]));
  const col = d3.scaleOrdinal().domain(keys).range(["#9ecae1", "#c2eabd"]);

  const layers = plot.selectAll("path.layer").data(stack, d=>d.key);
  layers.join(
    enter => enter.append("path").attr("class","layer")
      .attr("fill", d => col(d.key)).attr("d", area).attr("opacity",0)
      .transition().duration(DUR).ease(d3.easeCubicInOut).attr("opacity",.95),
    update => update.transition().duration(DUR).ease(d3.easeCubicInOut).attr("d", area),
    exit => exit.transition().duration(300).attr("opacity",0).remove()
  );

  xAxisG.transition().duration(DUR).ease(d3.easeCubicInOut)
    .call(d3.axisBottom(x).ticks(d3.timeMonth.every(1)).tickFormat(monthFmt));
  yAxisG.transition().duration(DUR).ease(d3.easeCubicInOut)
    .call(d3.axisLeft(y).ticks(5));

  xLabel.text("Date");
  yLabel.text("Stacked value");

  // legend
  if (legend.select(".legend-title").empty()){
    legend.append("text").attr("class","legend-title").attr("x",0).attr("y",-6).text("Variables");
  }
  const items = legend.selectAll("g.item").data(keys, d=>d);
  const enter = items.enter().append("g").attr("class","item");
  enter.append("rect").attr("width",12).attr("height",12);
  enter.append("text").attr("x",18).attr("y",10);
  items.merge(enter)
    .attr("transform",(d,i)=>`translate(0, ${i*18})`)
    .select("rect").attr("fill", d => col(d));
  items.merge(enter)
    .select("text").text(d=>d);
}

// ==== Scatter ====
function renderScatter(){
  const {plot, xAxisG, yAxisG, xLabel, yLabel, legend, w, h} = getRef("#scatter");

  const x = d3.scaleLinear().domain(d3.extent(state.rows, d=>d.ridership)).nice().range([0,w]);
  const y = d3.scaleLinear().domain(d3.extent(state.rows, d=>d.on_time_pct)).nice().range([h,0]);

  const dots = plot.selectAll("circle.dot").data(state.rows, d=>+d.date);
  dots.join(
    enter => enter.append("circle").attr("class","dot")
      .attr("r",5).attr("stroke","#fff").attr("stroke-width",1.2)
      .attr("cx", d=>x(d.ridership)).attr("cy", d=>y(d.on_time_pct))
      .attr("fill", d=>dayTypeColor(d.day_type)).attr("opacity",0)
      .transition().duration(300).ease(d3.easeCubicInOut).attr("opacity",.9),
    update => update.transition().duration(DUR).ease(d3.easeCubicInOut)
      .attr("cx", d=>x(d.ridership)).attr("cy", d=>y(d.on_time_pct)),
    exit => exit.transition().duration(250).attr("opacity",0).remove()
  );

  xAxisG.transition().duration(DUR).ease(d3.easeCubicInOut)
    .call(d3.axisBottom(x).ticks(6).tickFormat(fmtInt));
  yAxisG.transition().duration(DUR).ease(d3.easeCubicInOut)
    .call(d3.axisLeft(y).ticks(5).tickFormat(d=>fmtPct(d)+"%"));

  xLabel.text("Ridership (passengers/day)");
  yLabel.text("On-time performance (%)");

  // legend
  if (legend.select(".legend-title").empty()){
    legend.append("text").attr("class","legend-title").attr("x",0).attr("y",-6").text("Day type");
  }
  const cats = dayTypeColor.domain();
  const items = legend.selectAll("g.item").data(cats, d=>d);
  const enter = items.enter().append("g").attr("class","item");
  enter.append("rect").attr("width",12).attr("height",12);
  enter.append("text").attr("x",18).attr("y",10);
  items.merge(enter)
    .attr("transform",(d,i)=>`translate(0, ${i*18})`)
    .select("rect").attr("fill", d => dayTypeColor(d));
  items.merge(enter)
    .select("text").text(d=>d);
}
