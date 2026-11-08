"use strict";
const specimenData = JSON.parse(document.getElementById("specimen-data").textContent);
const fields = Object.fromEntries(["text-input", "format", "size", "size-label", "alternate", "kern", "reverse", "preview", "unsupported", "font-status", "reset", "reading-size", "leading", "paragraphs"].map(id => [id, document.getElementById(id)]));
const encoded = new Set(specimenData.encoded);
const defaults = { text: specimenData.article.paragraphs[0], format: "otf", size: 32 };
let loadSequence = 0;

function updatePreview() {
  fields.preview.textContent = fields["text-input"].value;
  fields.preview.style.fontSize = fields.size.value + "px";
  fields["size-label"].value = fields.size.value + "px";
  fields.preview.classList.toggle("alternate", fields.alternate.checked);
  fields.preview.style.fontKerning = fields.kern.checked ? "normal" : "none";
  document.body.classList.toggle("reversed", fields.reverse.checked);
  const missing = [...new Set([...fields["text-input"].value].filter(char => !encoded.has(char.codePointAt(0)) && char !== "\n" && char !== "\r"))];
  fields.unsupported.hidden = missing.length === 0;
  fields.unsupported.textContent = missing.length ? "未収録の文字は別のフォントで表示されます：" + missing.slice(0, 16).join(" ") + (missing.length > 16 ? " …" : "") : "";
}

async function updateFormat() {
  const sequence = ++loadSequence;
  const family = fields.format.value === "otf" ? "SuginamiOTF" : "SuginamiTTF";
  document.documentElement.style.setProperty("--face", family);
  fields["font-status"].textContent = "読込中…";
  try {
    const faces = await document.fonts.load("700 64px " + family, "Type freely");
    if (sequence === loadSequence) fields["font-status"].textContent = faces.length ? fields.format.value.toUpperCase() + " 読込済み" : "フォント読込失敗";
  } catch (_) {
    if (sequence === loadSequence) fields["font-status"].textContent = "フォント読込失敗";
  }
}

function updateReading() {
  fields.paragraphs.style.fontSize = fields["reading-size"].value + "px";
  fields.paragraphs.style.lineHeight = fields.leading.value;
}

function reset() {
  fields["text-input"].value = defaults.text;
  fields.format.value = defaults.format;
  fields.size.value = defaults.size;
  fields.alternate.checked = false;
  fields.kern.checked = true;
  fields.reverse.checked = false;
  fields["reading-size"].value = "24";
  fields.leading.value = "1.6";
  updatePreview(); updateReading(); updateFormat();
}
fields["text-input"].addEventListener("input", updatePreview);
fields.size.addEventListener("input", updatePreview);
for (const name of ["alternate", "kern", "reverse"]) fields[name].addEventListener("change", updatePreview);
for (const name of ["reading-size", "leading"]) fields[name].addEventListener("change", updateReading);
fields.format.addEventListener("change", updateFormat);
fields.reset.addEventListener("click", reset);
reset();
