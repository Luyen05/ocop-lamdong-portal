import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";

const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/(.:)/, "$1")), "..");
const dataset = JSON.parse(await fs.readFile(path.join(repoRoot, "data", "ocop", "ocop_records.json"), "utf8"));
const manifestText = await fs.readFile(path.join(repoRoot, "data", "ocop", "source_manifest.csv"), "utf8");
const outputPath = path.join(repoRoot, "database", "seed_ocop_2025_2026.sql");

function parseCsvLine(line) {
  const fields = [];
  let current = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (char === '"') {
      if (quoted && line[index + 1] === '"') {
        current += '"';
        index += 1;
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
  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
  });
}

function q(value) {
  return value === null || value === undefined || value === ""
    ? "NULL"
    : `'${String(value).replaceAll("'", "''")}'`;
}

function bool(value) {
  return value ? "TRUE" : "FALSE";
}

function slugify(value) {
  return value.normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

const fixedSubjectEmails = new Map([
  ["Công ty TNHH Seagull", "public-reference-seagull@local.invalid"],
  ["Chi nhánh Công ty TNHH Nông Nghiệp Ceres", "public-reference-ceres@local.invalid"],
  ["Hợp tác xã Nông sản Hữu cơ Bechamp Đắk Nông", "public-reference-bechamp@local.invalid"],
  ["Công ty TNHH Atiso Hoàng An Đà Lạt", "public-reference-hoang-an@local.invalid"],
]);

function subjectEmail(name) {
  if (fixedSubjectEmails.has(name)) return fixedSubjectEmails.get(name);
  const hash = crypto.createHash("sha256").update(name).digest("hex").slice(0, 12);
  return `ocop-source-${hash}@local.invalid`;
}

function subjectType(name) {
  if (/^(Hợp tác xã|HTX)/i.test(name)) return "cooperative";
  if (/^(Hộ kinh doanh|Cơ sở)/i.test(name)) return "household";
  return "company";
}

function categorySlug(category) {
  return new Map([
    ["Thực phẩm", "thuc-pham"],
    ["Đồ uống", "do-uong"],
    ["Thảo dược", "thao-duoc"],
  ]).get(category);
}

const sources = parseCsv(manifestText);
const sourceById = new Map(sources.map((source) => [source.source_id, source]));
const products = dataset.batches.flatMap((batch) => batch.products.map((product) => ({
  ...product,
  batch,
  slug: product.slug || `du-lieu-${slugify(product.record_id)}-${slugify(product.product_name)}`,
})));
const subjects = [...new Map(products.map((product) => [product.subject_name, product])).entries()]
  .map(([name, example]) => ({
    name,
    email: subjectEmail(name),
    type: subjectType(name),
    address: example.current_address,
    district: example.current_commune || "Chưa xác định",
  }));

const values = (rows) => rows.map((row) => `  (${row.join(", ")})`).join(",\n");
const passwordHash = "$argon2id$v=19$m=65536,t=3,p=4$1AXbivzI3q9g7C7t+AK3xw$tLhgXDoJ5dqNYxG+nCTIwFIoMMBaSu2+gcynwqteNVE";

const sourceRows = sources.map((source) => [
  q(source.title), q(source.document_number), q(source.issuing_body), q(source.source_type),
  source.published_at ? `${q(source.published_at)}::DATE` : "NULL::DATE", q(source.source_url),
  q(source.local_file), q(source.sha256), `${q(source.retrieved_at)}::DATE`,
]);

const userRows = subjects.map((subject) => [q(subject.email), q(`Dữ liệu mẫu - ${subject.name}`)]);
const subjectRows = subjects.map((subject) => [q(subject.email), q(subject.name), q(subject.type), q(subject.address), q(subject.district)]);

const productRows = products.map((product) => {
  const source = sourceById.get(product.batch.source_id);
  const description = `Sản phẩm OCOP ${product.product_name} của ${product.subject_name}. Dữ liệu mô tả tối thiểu được tổng hợp từ nguồn công khai và cần được chủ thể bổ sung trước khi dùng cho mục đích thương mại.`;
  const reviewNote = `Dữ liệu mẫu; nguồn ${product.batch.verification_level}: ${product.batch.source_id}. ${product.batch.batch_notes || "Đã đối chiếu quyết định chính thức."}`;
  const reviewDate = product.batch.cert_issued_at || source.published_at;
  return [
    q(subjectEmail(product.subject_name)), q(categorySlug(product.category)), q(product.product_name), q(product.slug),
    product.batch.star_rating, product.batch.cert_year, product.batch.cert_issued_at ? `${q(product.batch.cert_issued_at)}::DATE` : "NULL::DATE",
    product.batch.cert_expires_at ? `${q(product.batch.cert_expires_at)}::DATE` : "NULL::DATE", q(product.batch.issuing_authority),
    q(source.source_url), q(description), q(product.batch.publish_eligible ? "approved" : "pending"),
    `${q(reviewDate)}::TIMESTAMPTZ`, `${q(reviewDate)}::TIMESTAMPTZ`, q(reviewNote),
  ];
});

const productSourceRows = products.flatMap((product) => {
  const primarySource = sourceById.get(product.batch.source_id);
  const rows = [[
    q(product.slug), q(primarySource.source_url), q(product.batch.verification_level), q(product.original_address),
    q("recognition"), `${q(dataset.metadata.cutoff_date)}::DATE`, q(product.notes || product.batch.batch_notes || "Nguồn xác nhận chính."),
  ]];
  if (product.batch.secondary_source_id) {
    const secondarySource = sourceById.get(product.batch.secondary_source_id);
    rows.push([
      q(product.slug), q(secondarySource.source_url), q(secondarySource.verification_level), q(product.original_address),
      q("identity"), `${q(dataset.metadata.cutoff_date)}::DATE`, q("Nguồn nêu tên sản phẩm trong giai đoạn đề xuất; chỉ dùng để đối chiếu định danh."),
    ]);
  }
  return rows;
});

const imageRows = products.map((product) => [
  q(product.slug), q(`seed/ocop-2025-2026/${product.slug}.svg`), q("/assets/demo/products/public-reference.svg"),
  q(`Ảnh minh họa cho ${product.product_name}`),
]);

const sql = `-- Bộ dữ liệu mẫu OCOP Lâm Đồng 2025–2026 cho môi trường phát triển.
-- Sinh tự động từ data/ocop/ocop_records.json ngày ${dataset.metadata.cutoff_date}.
-- KHÔNG phải cơ sở dữ liệu hành chính chính thức và KHÔNG chạy trong production.
-- Giá chưa được nguồn công bố được lưu bằng 0, đơn vị "liên hệ chủ thể".
-- Tài khoản kỹ thuật dùng miền .invalid, bị khóa và không thể đăng nhập.

BEGIN;

INSERT INTO categories (name, slug, description, icon) VALUES
  ('Thực phẩm', 'thuc-pham', 'Sản phẩm thực phẩm OCOP', 'bi-basket'),
  ('Đồ uống', 'do-uong', 'Trà, cà phê và đồ uống OCOP', 'bi-cup-straw'),
  ('Thảo dược', 'thao-duoc', 'Sản phẩm từ dược liệu địa phương', 'bi-flower1')
ON CONFLICT (slug) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  icon = EXCLUDED.icon;

INSERT INTO users (role_id, email, hashed_password, full_name, is_active)
SELECT roles.id, 'public-reference-admin@local.invalid', ${q(passwordHash)},
       'Tài khoản nhập dữ liệu nguồn công khai', FALSE
FROM roles WHERE roles.name = 'admin'
ON CONFLICT (email) DO UPDATE SET
  role_id = EXCLUDED.role_id,
  full_name = EXCLUDED.full_name,
  is_active = FALSE;

WITH reference_users(email, full_name) AS (
VALUES
${values(userRows)}
)
INSERT INTO users (role_id, email, hashed_password, full_name, is_active)
SELECT roles.id, reference_users.email, ${q(passwordHash)}, reference_users.full_name, FALSE
FROM reference_users CROSS JOIN roles
WHERE roles.name = 'subject'
ON CONFLICT (email) DO UPDATE SET
  role_id = EXCLUDED.role_id,
  full_name = EXCLUDED.full_name,
  is_active = FALSE;

WITH reference_subjects(user_email, name, type, address, district) AS (
VALUES
${values(subjectRows)}
)
INSERT INTO subjects (
  user_id, name, type, representative, phone, email, address, district,
  status, reviewed_by, reviewed_at, rejection_reason
)
SELECT subject_user.id, reference_subjects.name, reference_subjects.type,
       'Tài khoản kỹ thuật - không công khai', 'Không công khai', NULL,
       reference_subjects.address, reference_subjects.district, 'approved',
       import_admin.id, CURRENT_TIMESTAMP, NULL
FROM reference_subjects
JOIN users AS subject_user ON subject_user.email = reference_subjects.user_email
CROSS JOIN users AS import_admin
WHERE import_admin.email = 'public-reference-admin@local.invalid'
ON CONFLICT (user_id) DO UPDATE SET
  name = EXCLUDED.name,
  type = EXCLUDED.type,
  representative = EXCLUDED.representative,
  phone = EXCLUDED.phone,
  email = EXCLUDED.email,
  address = EXCLUDED.address,
  district = EXCLUDED.district,
  status = 'approved',
  reviewed_by = EXCLUDED.reviewed_by,
  reviewed_at = EXCLUDED.reviewed_at,
  rejection_reason = NULL;

WITH source_rows(
  title, document_number, issuing_body, source_type, published_at,
  source_url, local_path, sha256, retrieved_at
) AS (
VALUES
${values(sourceRows)}
)
INSERT INTO data_sources (
  title, document_number, issuing_body, source_type, published_at,
  source_url, local_path, sha256, retrieved_at
)
SELECT * FROM source_rows
ON CONFLICT (source_url) DO UPDATE SET
  title = EXCLUDED.title,
  document_number = EXCLUDED.document_number,
  issuing_body = EXCLUDED.issuing_body,
  source_type = EXCLUDED.source_type,
  published_at = EXCLUDED.published_at,
  local_path = EXCLUDED.local_path,
  sha256 = EXCLUDED.sha256,
  retrieved_at = EXCLUDED.retrieved_at;

WITH product_rows(
  subject_user_email, category_slug, name, slug, star, cert_year,
  cert_issued_at, cert_expires_at, issuing_authority, certificate_url,
  description, status, submitted_at, reviewed_at, review_note
) AS (
VALUES
${values(productRows)}
)
INSERT INTO ocop_products (
  subject_id, category_id, name, slug, star, price, unit, cert_year,
  cert_issued_at, cert_expires_at, issuing_authority, certificate_url,
  description, status, submitted_at, reviewed_by, reviewed_at, review_note
)
SELECT subjects.id, categories.id, product_rows.name, product_rows.slug,
       product_rows.star, 0, 'liên hệ chủ thể', product_rows.cert_year,
       product_rows.cert_issued_at, product_rows.cert_expires_at,
       product_rows.issuing_authority, product_rows.certificate_url,
       product_rows.description, product_rows.status, product_rows.submitted_at,
       import_admin.id, product_rows.reviewed_at, product_rows.review_note
FROM product_rows
JOIN users AS subject_user ON subject_user.email = product_rows.subject_user_email
JOIN subjects ON subjects.user_id = subject_user.id
JOIN categories ON categories.slug = product_rows.category_slug
CROSS JOIN users AS import_admin
WHERE import_admin.email = 'public-reference-admin@local.invalid'
ON CONFLICT (slug) DO UPDATE SET
  subject_id = EXCLUDED.subject_id,
  category_id = EXCLUDED.category_id,
  name = EXCLUDED.name,
  star = EXCLUDED.star,
  price = 0,
  unit = EXCLUDED.unit,
  cert_year = EXCLUDED.cert_year,
  cert_issued_at = EXCLUDED.cert_issued_at,
  cert_expires_at = EXCLUDED.cert_expires_at,
  issuing_authority = EXCLUDED.issuing_authority,
  certificate_url = EXCLUDED.certificate_url,
  description = EXCLUDED.description,
  status = EXCLUDED.status,
  submitted_at = EXCLUDED.submitted_at,
  reviewed_by = EXCLUDED.reviewed_by,
  reviewed_at = EXCLUDED.reviewed_at,
  review_note = EXCLUDED.review_note;

WITH source_links(
  product_slug, source_url, verification_level, original_address,
  evidence_role, verified_at, notes
) AS (
VALUES
${values(productSourceRows)}
)
INSERT INTO product_sources (
  product_id, source_id, verification_level, original_address,
  evidence_role, verified_at, notes
)
SELECT products.id, sources.id, source_links.verification_level,
       source_links.original_address, source_links.evidence_role,
       source_links.verified_at, source_links.notes
FROM source_links
JOIN ocop_products AS products ON products.slug = source_links.product_slug
JOIN data_sources AS sources ON sources.source_url = source_links.source_url
ON CONFLICT (product_id, source_id, evidence_role) DO UPDATE SET
  verification_level = EXCLUDED.verification_level,
  original_address = EXCLUDED.original_address,
  verified_at = EXCLUDED.verified_at,
  notes = EXCLUDED.notes;

WITH placeholder_images(product_slug, storage_path, image_url, alt_text) AS (
VALUES
${values(imageRows)}
)
INSERT INTO product_images (
  product_id, storage_path, image_url, alt_text, is_primary, sort_order
)
SELECT products.id, placeholder_images.storage_path, placeholder_images.image_url,
       placeholder_images.alt_text, TRUE, 0
FROM placeholder_images
JOIN ocop_products AS products ON products.slug = placeholder_images.product_slug
ON CONFLICT DO NOTHING;

COMMIT;
`;

await fs.writeFile(outputPath, sql, "utf8");
console.log(JSON.stringify({ outputPath, products: products.length, subjects: subjects.length, sources: sources.length, links: productSourceRows.length }));
