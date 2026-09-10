import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(.:)/, "$1")), "..");
const dataPath = path.join(repoRoot, "data", "ocop", "ocop_records.json");
const manifestPath = path.join(repoRoot, "data", "ocop", "source_manifest.csv");
const outputPath = path.join(repoRoot, "data", "ocop", "ocop_lamdong_2025_2026.xlsx");
const renderDir = path.join(repoRoot, ".tmp", "ocop_workbook_render");

const FONT = "Segoe UI";
const COLORS = {
  green: "#006045",
  greenDark: "#004F3B",
  greenLight: "#DDF4EA",
  gold: "#FFB900",
  navy: "#0F172B",
  slate: "#62748E",
  surface: "#F8FAFC",
  border: "#D9E2EC",
  white: "#FFFFFF",
  warning: "#FFF4CE",
  error: "#FDE7E9",
};

function parseCsvLine(line) {
  const fields = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      if (quoted && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        quoted = !quoted;
      }
    } else if (char === "," && !quoted) {
      fields.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  fields.push(current);
  return fields;
}

function parseCsv(text) {
  const lines = text.replace(/^\uFEFF/, "").trim().split(/\r?\n/);
  const headers = parseCsvLine(lines[0]);
  return lines.slice(1).filter(Boolean).map((line) => {
    const values = parseCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
  });
}

function excelDate(value) {
  return value ? new Date(`${value}T00:00:00`) : null;
}

function expandProducts(dataset) {
  return dataset.batches.flatMap((batch) => batch.products.map((product) => ({
    record_id: product.record_id,
    product_name: product.product_name,
    subject_name: product.subject_name,
    category: product.category,
    star_rating: batch.star_rating,
    cert_year: batch.cert_year,
    decision_number: batch.decision_number,
    cert_issued_at: excelDate(batch.cert_issued_at),
    cert_expires_at: excelDate(batch.cert_expires_at),
    issuing_authority: batch.issuing_authority,
    original_address: product.original_address,
    current_address: product.current_address,
    legacy_region: batch.legacy_region,
    current_commune: product.current_commune,
    source_id: batch.source_id,
    verification_level: batch.verification_level,
    verification_status: batch.verification_status,
    publish_eligible: batch.publish_eligible,
    description: `Sản phẩm OCOP ${product.product_name} của ${product.subject_name}. Thông tin mô tả đang được hoàn thiện từ nguồn do chủ thể cung cấp.`,
    image_source_url: "",
    image_permission: "placeholder_only",
    notes: [batch.batch_notes, product.notes].filter(Boolean).join(" "),
  })));
}

function addTitle(sheet, title, subtitle, endColumn) {
  sheet.mergeCells(`A1:${endColumn}1`);
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${endColumn}1`).format = {
    fill: COLORS.greenDark,
    font: { name: FONT, size: 18, bold: true, color: COLORS.white },
    verticalAlignment: "center",
  };
  sheet.getRange(`A1:${endColumn}1`).format.rowHeight = 34;
  sheet.mergeCells(`A2:${endColumn}2`);
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A2:${endColumn}2`).format = {
    fill: COLORS.greenLight,
    font: { name: FONT, size: 10, color: COLORS.greenDark, italic: true },
    wrapText: true,
    verticalAlignment: "center",
  };
  sheet.getRange(`A2:${endColumn}2`).format.rowHeight = 30;
  sheet.showGridLines = false;
}

function styleHeader(range) {
  range.format = {
    fill: COLORS.green,
    font: { name: FONT, size: 10, bold: true, color: COLORS.white },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "all", style: "thin", color: COLORS.border },
  };
  range.format.rowHeight = 34;
}

function styleBody(range) {
  range.format = {
    font: { name: FONT, size: 9, color: COLORS.navy },
    wrapText: true,
    verticalAlignment: "top",
    borders: { preset: "all", style: "thin", color: COLORS.border },
  };
}

const dataset = JSON.parse(await fs.readFile(dataPath, "utf8"));
const sources = parseCsv(await fs.readFile(manifestPath, "utf8"));
const products = expandProducts(dataset);
const workbook = Workbook.create();
const readme = workbook.worksheets.add("README");
const productSheet = workbook.worksheets.add("PRODUCTS");
const sourceSheet = workbook.worksheets.add("SOURCES");
const mappingSheet = workbook.worksheets.add("ADMIN_MAPPING");
const issueSheet = workbook.worksheets.add("ISSUES");

// README
addTitle(readme, "BỘ DỮ LIỆU MẪU OCOP LÂM ĐỒNG 2025–2026", `Chốt dữ liệu ngày ${dataset.metadata.cutoff_date} · Dùng cho đồ án và kiểm thử`, "F");
readme.getRange("A4:B9").values = [
  ["Phạm vi", dataset.metadata.geographic_scope],
  ["Thời gian nguồn", "Nguồn được công bố từ 01/01/2025 đến ngày chốt dữ liệu; năm chứng nhận được giữ đúng theo nguồn."],
  ["Phương pháp", "Ưu tiên quyết định có phụ lục; đối chiếu báo/cổng cơ quan nhà nước; lưu địa chỉ gốc và chỉ ghi địa chỉ hiện hành khi có căn cứ pháp lý."],
  ["Ảnh", "Không tải hàng loạt ảnh báo chí. Khi chưa có quyền sử dụng rõ ràng, hệ thống dùng ảnh placeholder."],
  ["Tuyên bố", dataset.metadata.disclaimer],
  ["Cấu trúc", "PRODUCTS: sản phẩm; SOURCES: nguồn; ADMIN_MAPPING: ánh xạ địa chỉ; ISSUES: vấn đề cần xác minh."],
];
styleBody(readme.getRange("A4:B9"));
readme.getRange("A4:A9").format = { fill: COLORS.surface, font: { name: FONT, size: 10, bold: true, color: COLORS.greenDark } };
readme.getRange("D4:E4").values = [["Chỉ số", "Giá trị"]];
styleHeader(readme.getRange("D4:E4"));
readme.getRange("D5:D10").values = [["Tổng sản phẩm"], ["Nguồn cấp A"], ["Nguồn cấp B1"], ["Sản phẩm 3 sao"], ["Sản phẩm 4 sao"], ["Đủ điều kiện công khai"]];
readme.getRange("E5:E10").formulas = [
  ["=COUNTA(PRODUCTS!A5:A200)"],
  ["=COUNTIF(PRODUCTS!P5:P200,\"A\")"],
  ["=COUNTIF(PRODUCTS!P5:P200,\"B1\")"],
  ["=COUNTIF(PRODUCTS!E5:E200,3)"],
  ["=COUNTIF(PRODUCTS!E5:E200,4)"],
  ["=COUNTIF(PRODUCTS!P5:P200,\"A\")+COUNTIF(PRODUCTS!P5:P200,\"B1\")"],
];
styleBody(readme.getRange("D5:E10"));
readme.getRange("A12:F12").values = [["Cấp nguồn", "Ý nghĩa", "Được xác nhận sao?", "Công khai?", "Ví dụ", "Lưu ý"]];
styleHeader(readme.getRange("A12:F12"));
readme.getRange("A13:F16").values = [
  ["A", "Quyết định chính thức có chữ ký/phụ lục", "Có", "Có", "3981/QĐ-UBND", "Ưu tiên cao nhất"],
  ["B1", "Báo/cổng nhà nước xác nhận đã công nhận/trao giấy", "Có, theo nội dung nguồn", "Có thể", "Báo Lâm Đồng", "Cần bổ sung quyết định khi tìm được"],
  ["B2", "Đề xuất, đánh giá hoặc chấm điểm", "Chưa", "Không", "Bài đánh giá", "Chỉ dùng trạng thái pending"],
  ["C", "Website chủ thể", "Không", "Không tự xác nhận", "Trang sản phẩm", "Chỉ bổ sung mô tả/quy cách/ảnh"],
];
styleBody(readme.getRange("A13:F16"));
readme.getRange("A4:A16").format.columnWidth = 19;
readme.getRange("B4:B16").format.columnWidth = 62;
readme.getRange("C4:F16").format.columnWidth = 22;
readme.freezePanes.freezeRows(2);
readme.tabColor = COLORS.greenDark;

// PRODUCTS
const productHeaders = ["record_id", "product_name", "subject_name", "category", "star_rating", "cert_year", "decision_number", "cert_issued_at", "cert_expires_at", "issuing_authority", "original_address", "current_address", "legacy_region", "current_commune", "source_id", "verification_level", "verification_status", "publish_eligible", "description", "image_source_url", "image_permission", "notes"];
addTitle(productSheet, "DANH SÁCH SẢN PHẨM OCOP", `${products.length} bản ghi chuẩn hóa; dữ liệu rỗng thể hiện nguồn chưa công bố, không phải giá trị bằng 0.`, "V");
productSheet.getRange("A4:V4").values = [productHeaders];
styleHeader(productSheet.getRange("A4:V4"));
const productRows = products.map((product) => productHeaders.map((key) => product[key] ?? ""));
productSheet.getRange(`A5:V${productRows.length + 4}`).values = productRows;
styleBody(productSheet.getRange(`A5:V${productRows.length + 4}`));
productSheet.getRange(`E5:F${productRows.length + 4}`).format.numberFormat = "0";
productSheet.getRange(`H5:I${productRows.length + 4}`).format.numberFormat = "yyyy-mm-dd";
productSheet.getRange(`R5:R${productRows.length + 4}`).format.horizontalAlignment = "center";
productSheet.tables.add(`A4:V${productRows.length + 4}`, true, "OcopProductsTable").style = "TableStyleMedium4";
productSheet.freezePanes.freezeRows(4);
productSheet.freezePanes.freezeColumns(2);
productSheet.getRange("A:V").format.columnWidth = 15;
productSheet.getRange("B:C").format.columnWidth = 30;
productSheet.getRange("G:J").format.columnWidth = 18;
productSheet.getRange("K:L").format.columnWidth = 42;
productSheet.getRange("Q:Q").format.columnWidth = 26;
productSheet.getRange("S:S").format.columnWidth = 46;
productSheet.getRange("T:T").format.columnWidth = 28;
productSheet.getRange("V:V").format.columnWidth = 55;
productSheet.tabColor = COLORS.green;

// SOURCES
const sourceHeaders = ["source_id", "title", "document_number", "issuing_body", "published_at", "source_type", "source_url", "local_file", "retrieved_at", "sha256", "verification_level"];
addTitle(sourceSheet, "DANH MỤC NGUỒN", `${sources.length} nguồn; chỉ PDF hành chính quan trọng được lưu cục bộ trong repository.`, "K");
sourceSheet.getRange("A4:K4").values = [sourceHeaders];
styleHeader(sourceSheet.getRange("A4:K4"));
const sourceRows = sources.map((source) => sourceHeaders.map((key) => key.endsWith("_at") ? excelDate(source[key]) : source[key]));
sourceSheet.getRange(`A5:K${sourceRows.length + 4}`).values = sourceRows;
styleBody(sourceSheet.getRange(`A5:K${sourceRows.length + 4}`));
sourceSheet.getRange(`E5:E${sourceRows.length + 4}`).format.numberFormat = "yyyy-mm-dd";
sourceSheet.getRange(`I5:I${sourceRows.length + 4}`).format.numberFormat = "yyyy-mm-dd";
sourceSheet.tables.add(`A4:K${sourceRows.length + 4}`, true, "OcopSourcesTable").style = "TableStyleMedium4";
sourceSheet.freezePanes.freezeRows(4);
sourceSheet.freezePanes.freezeColumns(1);
sourceSheet.getRange("A:K").format.columnWidth = 18;
sourceSheet.getRange("B:B").format.columnWidth = 46;
sourceSheet.getRange("D:D").format.columnWidth = 28;
sourceSheet.getRange("G:G").format.columnWidth = 60;
sourceSheet.getRange("H:H").format.columnWidth = 40;
sourceSheet.getRange("J:J").format.columnWidth = 42;
sourceSheet.tabColor = "#0084D1";

// ADMIN_MAPPING
const mappingHeaders = ["old_province", "old_district", "old_commune", "current_province", "current_commune", "legal_source", "verified_at"];
addTitle(mappingSheet, "ÁNH XẠ ĐƠN VỊ HÀNH CHÍNH", "Địa chỉ gốc được giữ nguyên; địa chỉ hiện hành chỉ dùng khi đã đối chiếu Nghị quyết 1671/NQ-UBTVQH15.", "G");
mappingSheet.getRange("A4:G4").values = [mappingHeaders];
styleHeader(mappingSheet.getRange("A4:G4"));
const mappingRows = dataset.admin_mappings.map((mapping) => mappingHeaders.map((key) => key === "verified_at" ? excelDate(mapping[key]) : mapping[key]));
mappingSheet.getRange(`A5:G${mappingRows.length + 4}`).values = mappingRows;
styleBody(mappingSheet.getRange(`A5:G${mappingRows.length + 4}`));
mappingSheet.getRange(`G5:G${mappingRows.length + 4}`).format.numberFormat = "yyyy-mm-dd";
mappingSheet.tables.add(`A4:G${mappingRows.length + 4}`, true, "AdminMappingTable").style = "TableStyleMedium4";
mappingSheet.freezePanes.freezeRows(4);
mappingSheet.getRange("A:G").format.columnWidth = 24;
mappingSheet.getRange("C:C").format.columnWidth = 30;
mappingSheet.getRange("E:E").format.columnWidth = 32;
mappingSheet.tabColor = COLORS.gold;

// ISSUES
const issues = [];
for (const batch of dataset.batches) {
  if (!batch.decision_number) {
    issues.push([`ISSUE-${issues.length + 1}`, batch.batch_id, "Thiếu quyết định", "Cao", "Chưa tìm được số và phụ lục quyết định gốc.", "Tìm tại cổng văn bản/cơ quan ban hành; chưa tự suy luận ngày cấp.", batch.source_id, "open"]);
  }
  if (!batch.cert_issued_at) {
    issues.push([`ISSUE-${issues.length + 1}`, batch.batch_id, "Thiếu ngày cấp", "Cao", "Nguồn chỉ nêu ngày đăng hoặc ngày trao chứng nhận.", "Để trống cert_issued_at và cert_expires_at cho đến khi có quyết định.", batch.source_id, "open"]);
  }
  for (const product of batch.products) {
    if (!product.current_commune) {
      issues.push([`ISSUE-${issues.length + 1}`, product.record_id, "Thiếu xã/phường hiện tại", "Trung bình", product.notes || "Chưa đủ địa chỉ cấp xã để ánh xạ.", "Xác minh từ hồ sơ chủ thể hoặc phụ lục quyết định.", batch.source_id, "open"]);
    }
  }
}
issues.push([`ISSUE-${issues.length + 1}`, "TOAN-BO-DU-LIEU", "Ảnh chưa rõ quyền sử dụng", "Trung bình", "Không sử dụng ảnh báo chí hoặc ảnh chủ thể khi chưa có giấy phép rõ ràng.", "Dùng placeholder; thay bằng ảnh do chủ thể cung cấp hoặc được cấp phép.", "", "controlled"]);
issues.push([`ISSUE-${issues.length + 1}`, "TANHLINH-2025", "Năm chứng nhận ngoài khoảng", "Thấp", "Ba sản phẩm được bài năm 2025 nêu là công nhận trong đợt cuối năm 2024.", "Giữ cert_year=2024 và ghi chú minh bạch; không đổi thành 2025.", "SRC-B1-TANHLINH-2025", "documented"]);
const issueHeaders = ["issue_id", "record_or_batch", "issue_type", "severity", "description", "recommended_action", "source_id", "status"];
addTitle(issueSheet, "CÁC VẤN ĐỀ CẦN XÁC MINH", "Danh sách này ngăn dữ liệu chưa đủ chứng cứ bị hiểu nhầm là dữ liệu hành chính chính thức.", "H");
issueSheet.getRange("A4:H4").values = [issueHeaders];
styleHeader(issueSheet.getRange("A4:H4"));
issueSheet.getRange(`A5:H${issues.length + 4}`).values = issues;
styleBody(issueSheet.getRange(`A5:H${issues.length + 4}`));
issueSheet.tables.add(`A4:H${issues.length + 4}`, true, "OcopIssuesTable").style = "TableStyleMedium4";
issueSheet.freezePanes.freezeRows(4);
issueSheet.getRange("A:H").format.columnWidth = 22;
issueSheet.getRange("E:F").format.columnWidth = 52;
issueSheet.getRange("D:D").conditionalFormats.add("containsText", { text: "Cao", format: { fill: COLORS.error, font: { color: "#A4262C", bold: true } } });
issueSheet.getRange("D:D").conditionalFormats.add("containsText", { text: "Trung bình", format: { fill: COLORS.warning, font: { color: "#8A6D00", bold: true } } });
issueSheet.tabColor = "#D13438";

workbook.recalculate();
await fs.mkdir(path.dirname(outputPath), { recursive: true });
await fs.mkdir(renderDir, { recursive: true });

const inspection = await workbook.inspect({ kind: "workbook,sheet,table", maxChars: 8000, tableMaxRows: 4, tableMaxCols: 6, tableMaxCellChars: 60 });
console.log(inspection.ndjson);
for (const sheetName of ["README", "PRODUCTS", "SOURCES", "ADMIN_MAPPING", "ISSUES"]) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(renderDir, `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
}
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
await fs.rm(`${outputPath}.inspect.ndjson`, { force: true });
console.log(JSON.stringify({ outputPath, renderDir, products: products.length, sources: sources.length, issues: issues.length }));
