const schemaInput = document.getElementById("schemaInput");
const generateBtn = document.getElementById("generateBtn");
const loadExampleBtn = document.getElementById("loadExampleBtn");
const formatBtn = document.getElementById("formatSchemaBtn");
const copyBtn = document.getElementById("copySchemaBtn");
const statusEl = document.getElementById("schemaStatus");
const datasetNameInput = document.getElementById("datasetName");
const seedInput = document.getElementById("seedInput");
const modeInput = document.getElementById("modeInput");
const formatInput = document.getElementById("formatInput");
const boundaryToggle = document.getElementById("boundaryToggle");
const nullToggle = document.getElementById("nullToggle");
const invalidToggle = document.getElementById("invalidToggle");
const tableSelect = document.getElementById("tableSelect");
const previewTable = document.getElementById("previewTable");
const reportSummary = document.getElementById("reportSummary");
const coverageBars = document.getElementById("coverageBars");
const rulesList = document.getElementById("rulesList");
const datasetIdEl = document.getElementById("datasetId");
const configHashEl = document.getElementById("configHash");
const rowCountEl = document.getElementById("rowCount");
const repairCountEl = document.getElementById("repairCount");
const coverageCountEl = document.getElementById("coverageCount");
const violationCountEl = document.getElementById("violationCount");
const modeChip = document.getElementById("modeChip");
const seedChip = document.getElementById("seedChip");
const tableCount = document.getElementById("tableCount");
const downloadCsvBtn = document.getElementById("downloadCsvBtn");
const downloadJsonBtn = document.getElementById("downloadJsonBtn");

const exampleSchema = `dataset:
  name: ecommerce
  seed: 4242
  mode: valid
  size:
    customers: 100
    orders: 300
    order_items: 800
  max_attempts: 25

tables:
  customers:
    primary_key: customer_id
    columns:
      customer_id:
        type: uuid
      name:
        type: name
      email:
        type: email
        unique: true
      phone:
        type: phone
        nullable: true
      country:
        type: country
      postcode:
        type: postcode_uk
        nullable: true
      created_at:
        type: datetime
        range: ["2023-01-01T00:00:00", "2025-01-01T00:00:00"]
  orders:
    primary_key: order_id
    foreign_keys:
      - column: customer_id
        ref_table: customers
        ref_column: customer_id
    columns:
      order_id:
        type: uuid
      customer_id:
        type: uuid
      status:
        type: enum
        values: [PAID, FAILED, REFUNDED]
        weights: [0.7, 0.2, 0.1]
      total_amount:
        type: decimal
        range: [0, 2000]
        distribution: lognormal
      created_at:
        type: datetime
        range: ["2023-01-01T00:00:00", "2025-01-01T00:00:00"]
  order_items:
    primary_key: item_id
    foreign_keys:
      - column: order_id
        ref_table: orders
        ref_column: order_id
    columns:
      item_id:
        type: uuid
      order_id:
        type: uuid
      sku:
        type: text
        regex: "[A-Z]{3}-[0-9]{4}"
      quantity:
        type: int
        range: [1, 10]
      unit_price:
        type: decimal
        range: [1, 250]
      total_price:
        type: decimal
        range: [1, 2500]

rules:
  - if: "orders.status == 'FAILED'"
    then:
      - "orders.total_amount <= 500.0"
`;

schemaInput.value = exampleSchema;

let currentDataset = null;

class RNG {
  constructor(seed) {
    this.seed = seed >>> 0;
  }
  next() {
    this.seed += 0x6d2b79f5;
    let t = this.seed;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  int(min, max) {
    return Math.floor(this.next() * (max - min + 1)) + min;
  }
  float(min, max) {
    return this.next() * (max - min) + min;
  }
  choice(arr) {
    return arr[this.int(0, arr.length - 1)];
  }
  choices(arr, weights) {
    const total = weights.reduce((acc, val) => acc + val, 0);
    let roll = this.next() * total;
    for (let i = 0; i < arr.length; i += 1) {
      roll -= weights[i];
      if (roll <= 0) return arr[i];
    }
    return arr[arr.length - 1];
  }
  gaussian() {
    let u = 0;
    let v = 0;
    while (u === 0) u = this.next();
    while (v === 0) v = this.next();
    return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  }
}

const names = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Riley", "Jamie", "Casey", "Avery", "Quinn"];
const surnames = ["Smith", "Patel", "Kim", "Garcia", "Brown", "Jones", "Miller", "Davis", "Wilson", "Clark"];
const domains = ["example.com", "test.local", "sample.org", "demo.dev"];
const countries = ["United Kingdom", "United States", "Canada", "Germany", "France", "Australia", "Japan", "Brazil"];
const ukAreas = ["SW", "SE", "NW", "NE", "EC", "WC", "W", "E", "N", "S", "B", "M", "L", "G", "EH"];

function parseSchema(text) {
  const trimmed = text.trim();
  let raw;
  try {
    if (trimmed.startsWith("{")) {
      raw = JSON.parse(trimmed);
    } else if (window.jsyaml) {
      raw = window.jsyaml.load(trimmed);
    } else {
      throw new Error("YAML parser not available");
    }
  } catch (err) {
    throw new Error(`Schema parse error: ${err.message}`);
  }
  if (!raw || typeof raw !== "object") {
    throw new Error("Schema must be an object");
  }
  return normalizeSchema(raw);
}

function normalizeSchema(raw) {
  const dataset = raw.dataset || {};
  let size = dataset.size || {};
  if (typeof size === "number") {
    const tables = Object.keys(raw.tables || {});
    size = tables.reduce((acc, name) => ({ ...acc, [name]: size }), {});
  }
  const tables = {};
  Object.entries(raw.tables || {}).forEach(([name, table]) => {
    const columns = {};
    Object.entries(table.columns || {}).forEach(([colName, col]) => {
      columns[colName] = { name: colName, ...col };
    });
    tables[name] = {
      name,
      primary_key: table.primary_key,
      foreign_keys: table.foreign_keys || [],
      columns,
    };
  });
  return {
    dataset: {
      name: dataset.name || "dataset",
      seed: Number(dataset.seed ?? 1),
      mode: dataset.mode || "valid",
      size,
      max_attempts: Number(dataset.max_attempts ?? 10),
    },
    tables,
    rules: raw.rules || [],
  };
}

function planTables(schema) {
  const graph = new Map();
  const indegree = new Map();
  Object.keys(schema.tables).forEach((name) => {
    graph.set(name, new Set());
    indegree.set(name, 0);
  });
  Object.values(schema.tables).forEach((table) => {
    (table.foreign_keys || []).forEach((fk) => {
      if (!graph.has(fk.ref_table)) return;
      graph.get(fk.ref_table).add(table.name);
      indegree.set(table.name, indegree.get(table.name) + 1);
    });
  });
  const queue = Array.from(indegree.entries())
    .filter(([, deg]) => deg === 0)
    .map(([name]) => name);
  const order = [];
  while (queue.length) {
    const node = queue.shift();
    order.push(node);
    graph.get(node).forEach((child) => {
      indegree.set(child, indegree.get(child) - 1);
      if (indegree.get(child) === 0) queue.push(child);
    });
  }
  return order.length ? order : Object.keys(schema.tables);
}

function hashConfig(schema) {
  const json = JSON.stringify(schema);
  let hash = 0;
  for (let i = 0; i < json.length; i += 1) {
    hash = (hash << 5) - hash + json.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash).toString(16).padStart(8, "0");
}

function generateDataset(schema) {
  const order = planTables(schema);
  const pkPools = {};
  const rowsByTable = {};
  const repairCounts = {};
  const rng = new RNG(schema.dataset.seed);

  order.forEach((tableName) => {
    const table = schema.tables[tableName];
    const size = schema.dataset.size[tableName] || 10;
    pkPools[tableName] = [];
    rowsByTable[tableName] = [];
    repairCounts[tableName] = 0;

    const uniqueSets = {};
    Object.values(table.columns).forEach((col) => {
      if (col.unique) uniqueSets[col.name] = new Set();
    });
    const pkSet = new Set();

    for (let i = 0; i < size; i += 1) {
      const result = repairRow(() => buildRow(table, schema, rng, pkPools), (row) => rowValid(row, table, schema, uniqueSets, pkSet, pkPools), schema.dataset.max_attempts);
      repairCounts[tableName] += result.attempts;
      const row = result.row;
      registerRow(row, table, uniqueSets, pkSet, pkPools);
      rowsByTable[tableName].push(row);
    }
  });

  const report = validateDataset(schema, rowsByTable, pkPools, repairCounts);
  return {
    id: `synth-${Math.floor(rng.next() * 999999).toString().padStart(6, "0")}`,
    configHash: hashConfig(schema),
    order,
    rowsByTable,
    report,
  };
}

function repairRow(generateRow, validateRow, maxAttempts) {
  let attempts = 0;
  let row = {};
  while (attempts < maxAttempts) {
    attempts += 1;
    row = generateRow();
    if (validateRow(row)) return { row, attempts, success: true };
  }
  return { row, attempts, success: false };
}

function buildRow(table, schema, rng, pkPools) {
  const row = {};
  Object.values(table.columns).forEach((col) => {
    let value = generateValue(table, col, schema, rng, pkPools);
    value = applyEdgeCases(value, col, schema, rng);
    row[col.name] = value;
  });
  return row;
}

function generateValue(table, column, schema, rng, pkPools) {
  const fk = (table.foreign_keys || []).find((item) => item.column === column.name);
  if (fk) {
    if (schema.dataset.mode === "invalid" && rng.next() < 0.2) return "invalid_fk";
    const pool = pkPools[fk.ref_table] || [];
    return pool.length ? rng.choice(pool) : null;
  }
  switch (column.type) {
    case "uuid":
      return uuid(rng);
    case "int": {
      const [min, max] = column.range || [0, 1000];
      return intInRange(rng, min, max, column.distribution);
    }
    case "decimal": {
      const [min, max] = column.range || [0, 1000];
      return decimalInRange(rng, min, max, column.distribution);
    }
    case "bool":
      return rng.next() < 0.5;
    case "datetime": {
      const [start, end] = column.range || ["2023-01-01T00:00:00", "2025-01-01T00:00:00"];
      return randomDateTime(rng, start, end);
    }
    case "date": {
      const [start, end] = column.range || ["2023-01-01", "2025-01-01"];
      return randomDate(rng, start, end);
    }
    case "enum":
      if (column.values && column.weights) return rng.choices(column.values, column.weights);
      return column.values ? rng.choice(column.values) : "";
    case "text":
      if (column.regex) return textFromRegex(rng, column.regex);
      return randomText(rng, column.length);
    case "email":
      return `${rng.choice(names).toLowerCase()}.${rng.choice(surnames).toLowerCase()}@${rng.choice(domains)}`;
    case "phone":
      return `+${rng.int(1, 9)}${rng.int(100000000, 999999999)}`;
    case "country":
      return rng.choice(countries);
    case "postcode_uk":
      return `${rng.choice(ukAreas)}${rng.int(1, 9)} ${rng.int(0, 9)}${String.fromCharCode(rng.int(65, 90))}${String.fromCharCode(rng.int(65, 90))}`;
    case "name":
      return `${rng.choice(names)} ${rng.choice(surnames)}`;
    default:
      return "";
  }
}

function applyEdgeCases(value, column, schema, rng) {
  const mode = schema.dataset.mode;
  const invalidOn = invalidToggle.checked || mode === "invalid";
  if (invalidOn && rng.next() < 0.2) return invalidValue(column);

  if (column.nullable && nullToggle.checked && rng.next() < 0.12) return null;

  if (boundaryToggle.checked && rng.next() < 0.15) {
    return boundaryValue(value, column, rng);
  }
  return value;
}

function boundaryValue(value, column, rng) {
  if ((column.type === "int" || column.type === "decimal") && column.range) {
    return rng.next() < 0.5 ? column.range[0] : column.range[1];
  }
  if (column.type === "date" && column.range) {
    return rng.next() < 0.5 ? column.range[0] : column.range[1];
  }
  if (column.type === "datetime" && column.range) {
    return rng.next() < 0.5 ? column.range[0] : column.range[1];
  }
  if (column.type === "text" && column.length) {
    const target = rng.next() < 0.5 ? column.length[0] : column.length[1];
    return String(value || "").padEnd(target, "x").slice(0, target);
  }
  if (column.type === "enum" && column.values) {
    return rng.next() < 0.5 ? column.values[0] : column.values[column.values.length - 1];
  }
  return value;
}

function invalidValue(column) {
  switch (column.type) {
    case "int":
    case "decimal":
      return "not_a_number";
    case "date":
    case "datetime":
      return "not_a_date";
    case "bool":
      return "not_bool";
    case "enum":
      return "INVALID_ENUM";
    case "uuid":
      return "not-a-uuid";
    case "email":
      return "invalid-email";
    case "phone":
      return "invalid-phone";
    case "postcode_uk":
      return "INVALID";
    case "name":
      return "";
    case "text":
      return "!!!";
    default:
      return "invalid";
  }
}

function rowValid(row, table, schema, uniqueSets, pkSet, pkPools) {
  for (const column of Object.values(table.columns)) {
    const value = row[column.name];
    if (value === null || value === undefined) {
      if (!column.nullable) return false;
      continue;
    }
    if (column.unique && uniqueSets[column.name].has(value)) return false;
    if (column.name === table.primary_key && pkSet.has(value)) return false;
    if (column.type === "enum" && column.values && !column.values.includes(value)) return false;
    if (column.range && (column.type === "int" || column.type === "decimal")) {
      const min = Number(column.range[0]);
      const max = Number(column.range[1]);
      const num = Number(value);
      if (Number.isNaN(num) || num < min || num > max) return false;
    }
    if (column.regex && column.type === "text") {
      const regex = new RegExp(`^${column.regex}$`);
      if (!regex.test(String(value))) return false;
    }
    const fk = (table.foreign_keys || []).find((item) => item.column === column.name);
    if (fk) {
      const pool = pkPools[fk.ref_table] || [];
      if (!pool.includes(value)) return false;
    }
  }
  return true;
}

function registerRow(row, table, uniqueSets, pkSet, pkPools) {
  const pkValue = row[table.primary_key];
  if (pkValue != null) {
    pkSet.add(pkValue);
    pkPools[table.name].push(pkValue);
  }
  Object.entries(uniqueSets).forEach(([name, set]) => {
    const value = row[name];
    if (value != null) set.add(value);
  });
}

function validateDataset(schema, rowsByTable, pkPools, repairCounts) {
  let totalViolations = 0;
  const coverage = {};
  const tableReports = {};
  const rules = schema.rules || [];

  Object.entries(rowsByTable).forEach(([tableName, rows]) => {
    const table = schema.tables[tableName];
    const uniqueSets = {};
    Object.values(table.columns).forEach((col) => {
      if (col.unique) uniqueSets[col.name] = new Set();
    });

    const violations = {};
    let ruleViolations = 0;
    let failedRows = 0;

    rows.forEach((row) => {
      let rowFailed = false;
      Object.values(table.columns).forEach((column) => {
        increment(coverage, "type");
        let value = row[column.name];
        if (value === null || value === undefined) {
          increment(coverage, "nullable");
          if (!column.nullable) {
            increment(violations, "nullability");
            rowFailed = true;
          }
          return;
        }
        if (column.range && (column.type === "int" || column.type === "decimal")) {
          increment(coverage, "range");
          const num = Number(value);
          if (Number.isNaN(num) || num < column.range[0] || num > column.range[1]) {
            increment(violations, "range");
            rowFailed = true;
          }
        }
        if (column.regex && column.type === "text") {
          increment(coverage, "regex");
          const regex = new RegExp(`^${column.regex}$`);
          if (!regex.test(String(value))) {
            increment(violations, "regex");
            rowFailed = true;
          }
        }
        if (column.values && column.type === "enum") {
          increment(coverage, "enum");
          if (!column.values.includes(value)) {
            increment(violations, "enum");
            rowFailed = true;
          }
        }
        if (column.unique) {
          increment(coverage, "unique");
          if (uniqueSets[column.name].has(value)) {
            increment(violations, "unique");
            rowFailed = true;
          }
          uniqueSets[column.name].add(value);
        }
        const fk = (table.foreign_keys || []).find((item) => item.column === column.name);
        if (fk) {
          increment(coverage, "foreign_key");
          const pool = pkPools[fk.ref_table] || [];
          if (!pool.includes(value)) {
            increment(violations, "foreign_key");
            rowFailed = true;
          }
        }
      });

      if (rules.length) {
        increment(coverage, "rules");
        const ruleBroken = evaluateRules(rules, rowsByTable, row, tableName);
        if (ruleBroken) {
          ruleViolations += 1;
          rowFailed = true;
        }
      }

      if (rowFailed) failedRows += 1;
    });

    totalViolations += Object.values(violations).reduce((acc, val) => acc + val, 0) + ruleViolations;

    tableReports[tableName] = {
      table: tableName,
      row_count: rows.length,
      violations,
      rule_violations: ruleViolations,
      failed_rows: failedRows,
      repair_attempts: repairCounts[tableName] || 0,
    };
  });

  return {
    totalViolations,
    coverage,
    tableReports,
    rules,
  };
}

function evaluateRules(rules, rowsByTable, row, tableName) {
  let violation = false;
  const context = {};
  Object.keys(rowsByTable).forEach((key) => {
    context[key] = key === tableName ? row : {};
  });
  rules.forEach((rule) => {
    if (evalExpr(rule.if, context)) {
      rule.then.forEach((constraint) => {
        if (!evalExpr(constraint, context)) violation = true;
      });
    }
  });
  return violation;
}

function evalExpr(expr, context) {
  if (!expr) return false;
  const orParts = expr.split(/\s+or\s+/i);
  return orParts.some((part) => evalAnd(part, context));
}

function evalAnd(expr, context) {
  const andParts = expr.split(/\s+and\s+/i);
  return andParts.every((part) => evalCompare(part.trim(), context));
}

function evalCompare(expr, context) {
  const match = expr.match(/([\w]+)\.([\w]+)\s*(==|!=|<=|>=|<|>)\s*(.+)/);
  if (!match) return false;
  const [, table, column, op, rawValue] = match;
  const left = context?.[table]?.[column];
  const right = parseLiteral(rawValue.trim());
  switch (op) {
    case "==":
      return left == right;
    case "!=":
      return left != right;
    case "<=":
      return Number(left) <= Number(right);
    case ">=":
      return Number(left) >= Number(right);
    case "<":
      return Number(left) < Number(right);
    case ">":
      return Number(left) > Number(right);
    default:
      return false;
  }
}

function parseLiteral(raw) {
  if (raw.startsWith("'")) return raw.slice(1, -1);
  if (raw.startsWith('"')) return raw.slice(1, -1);
  const num = Number(raw);
  return Number.isNaN(num) ? raw : num;
}

function increment(counter, key) {
  counter[key] = (counter[key] || 0) + 1;
}

function uuid(rng) {
  const hex = [];
  for (let i = 0; i < 32; i += 1) {
    hex.push(Math.floor(rng.next() * 16).toString(16));
  }
  return `${hex.slice(0, 8).join("")}-${hex.slice(8, 12).join("")}-${hex.slice(12, 16).join("")}-${hex.slice(16, 20).join("")}-${hex.slice(20).join("")}`;
}

function intInRange(rng, min, max, distribution) {
  if (distribution === "normal") {
    const mean = (min + max) / 2;
    const sigma = (max - min) / 6 || 1;
    const val = Math.round(mean + rng.gaussian() * sigma);
    return clamp(val, min, max);
  }
  if (distribution === "lognormal") {
    const val = Math.exp(rng.gaussian());
    const scaled = min + (max - min) * (val / (1 + val));
    return clamp(Math.round(scaled), min, max);
  }
  return rng.int(min, max);
}

function decimalInRange(rng, min, max, distribution) {
  if (distribution === "normal") {
    const mean = (min + max) / 2;
    const sigma = (max - min) / 6 || 1;
    const val = mean + rng.gaussian() * sigma;
    return clamp(val, min, max);
  }
  if (distribution === "lognormal") {
    const val = Math.exp(rng.gaussian());
    const scaled = min + (max - min) * (val / (1 + val));
    return clamp(scaled, min, max);
  }
  return rng.float(min, max).toFixed(2);
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function randomDate(rng, start, end) {
  const startDate = new Date(start);
  const endDate = new Date(end);
  const ts = rng.float(startDate.getTime(), endDate.getTime());
  return new Date(ts).toISOString().slice(0, 10);
}

function randomDateTime(rng, start, end) {
  const startDate = new Date(start);
  const endDate = new Date(end);
  const ts = rng.float(startDate.getTime(), endDate.getTime());
  return new Date(ts).toISOString();
}

function randomText(rng, lengthRange) {
  const [min, max] = lengthRange || [5, 20];
  const len = rng.int(min, max);
  const alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ";
  let out = "";
  for (let i = 0; i < len; i += 1) {
    out += alphabet[rng.int(0, alphabet.length - 1)];
  }
  return out.trim() || "text";
}

function textFromRegex(rng, pattern) {
  if (pattern === "[A-Z]{3}-[0-9]{4}") {
    const letters = Array.from({ length: 3 }, () => String.fromCharCode(rng.int(65, 90))).join("");
    const numbers = Array.from({ length: 4 }, () => rng.int(0, 9)).join("");
    return `${letters}-${numbers}`;
  }
  return randomText(rng, [6, 10]);
}

function renderDataset(dataset, schema) {
  if (!dataset) return;
  const totalRows = Object.values(dataset.rowsByTable).reduce((acc, rows) => acc + rows.length, 0);
  datasetIdEl.textContent = dataset.id;
  configHashEl.textContent = dataset.configHash;
  rowCountEl.textContent = totalRows;
  repairCountEl.textContent = Object.values(dataset.report.tableReports).reduce((acc, val) => acc + val.repair_attempts, 0);
  coverageCountEl.textContent = Object.values(dataset.report.coverage).reduce((acc, val) => acc + val, 0);
  violationCountEl.textContent = `${dataset.report.totalViolations} violations`;

  modeChip.textContent = schema.dataset.mode;
  seedChip.textContent = schema.dataset.seed;
  tableCount.textContent = Object.keys(schema.tables).length;

  tableSelect.innerHTML = "";
  dataset.order.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    tableSelect.appendChild(option);
  });

  renderTable(dataset.rowsByTable[dataset.order[0]] || []);
  renderReport(dataset.report, schema);
}

function renderTable(rows) {
  if (!rows.length) {
    previewTable.innerHTML = "<tr><td>No rows generated</td></tr>";
    return;
  }
  const columns = Object.keys(rows[0]);
  const header = `<tr>${columns.map((col) => `<th>${col}</th>`).join("")}</tr>`;
  const body = rows.slice(0, 8).map((row) => {
    return `<tr>${columns.map((col) => `<td>${row[col] ?? ""}</td>`).join("")}</tr>`;
  }).join("");
  previewTable.innerHTML = header + body;
}

function renderReport(report, schema) {
  reportSummary.innerHTML = "";
  const entries = [
    ["Mode", schema.dataset.mode],
    ["Total violations", report.totalViolations],
    ["Tables", Object.keys(report.tableReports).length],
  ];
  entries.forEach(([label, value]) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${label}</span><span>${value}</span>`;
    reportSummary.appendChild(li);
  });

  coverageBars.innerHTML = "";
  const maxCoverage = Math.max(...Object.values(report.coverage), 1);
  Object.entries(report.coverage).forEach(([key, value]) => {
    const bar = document.createElement("div");
    bar.className = "bar";
    const label = document.createElement("span");
    label.textContent = `${key} (${value})`;
    const track = document.createElement("div");
    track.className = "bar-track";
    const fill = document.createElement("div");
    fill.className = "bar-fill";
    fill.style.width = `${(value / maxCoverage) * 100}%`;
    track.appendChild(fill);
    bar.appendChild(label);
    bar.appendChild(track);
    coverageBars.appendChild(bar);
  });

  rulesList.innerHTML = "";
  if (!report.rules.length) {
    rulesList.textContent = "No conditional rules defined.";
  } else {
    report.rules.forEach((rule) => {
      const div = document.createElement("div");
      div.textContent = `${rule.if} → ${rule.then.join(", ")}`;
      rulesList.appendChild(div);
    });
  }
}

function updateSchemaStatus(message, error = false) {
  statusEl.textContent = message;
  statusEl.style.color = error ? "#ff7f66" : "#52d6a6";
}

function handleGenerate() {
  try {
    const schema = parseSchema(schemaInput.value);
    schema.dataset.name = datasetNameInput.value || schema.dataset.name;
    schema.dataset.seed = Number(seedInput.value || schema.dataset.seed);
    schema.dataset.mode = modeInput.value;
    if (invalidToggle.checked) schema.dataset.mode = "invalid";

    updateSchemaStatus("Generating...", false);
    const dataset = generateDataset(schema);
    currentDataset = { dataset, schema };
    renderDataset(dataset, schema);
    updateSchemaStatus("Generated", false);
  } catch (err) {
    updateSchemaStatus(err.message, true);
  }
}

function handleDownloadCsv() {
  if (!currentDataset) return;
  const table = tableSelect.value || currentDataset.dataset.order[0];
  const rows = currentDataset.dataset.rowsByTable[table] || [];
  if (!rows.length) return;
  const columns = Object.keys(rows[0]);
  const lines = [columns.join(",")];
  rows.forEach((row) => {
    lines.push(columns.map((col) => formatCsvValue(row[col])).join(","));
  });
  downloadFile(`${table}.csv`, lines.join("\n"));
}

function handleDownloadJson() {
  if (!currentDataset) return;
  const table = tableSelect.value || currentDataset.dataset.order[0];
  const rows = currentDataset.dataset.rowsByTable[table] || [];
  if (!rows.length) return;
  const lines = rows.map((row) => JSON.stringify(row));
  downloadFile(`${table}.jsonl`, lines.join("\n"));
}

function formatCsvValue(value) {
  if (value === null || value === undefined) return "";
  const text = String(value);
  if (text.includes(",") || text.includes("\"")) {
    return `"${text.replace(/\"/g, '""')}"`;
  }
  return text;
}

function downloadFile(filename, content) {
  const blob = new Blob([content], { type: "text/plain" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

function handleTableChange() {
  if (!currentDataset) return;
  const table = tableSelect.value;
  renderTable(currentDataset.dataset.rowsByTable[table] || []);
}

function handleFormat() {
  try {
    const schema = parseSchema(schemaInput.value);
    schemaInput.value = window.jsyaml
      ? window.jsyaml.dump(schema, { noRefs: true, lineWidth: 100 })
      : JSON.stringify(schema, null, 2);
    updateSchemaStatus("Formatted", false);
  } catch (err) {
    updateSchemaStatus(err.message, true);
  }
}

function handleCopy() {
  navigator.clipboard.writeText(schemaInput.value).then(
    () => updateSchemaStatus("Copied", false),
    () => updateSchemaStatus("Copy failed", true)
  );
}

loadExampleBtn.addEventListener("click", () => {
  schemaInput.value = exampleSchema;
  updateSchemaStatus("Example loaded", false);
});

formatBtn.addEventListener("click", handleFormat);
copyBtn.addEventListener("click", handleCopy);

generateBtn.addEventListener("click", handleGenerate);

tableSelect.addEventListener("change", handleTableChange);

downloadCsvBtn.addEventListener("click", handleDownloadCsv);
downloadJsonBtn.addEventListener("click", handleDownloadJson);

handleGenerate();
