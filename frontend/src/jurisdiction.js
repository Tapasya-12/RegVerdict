// Maps a document/regulator name to one of 4 jurisdiction color slots
// (j1..j4, defined in index.css). Assignment is purely positional — the
// Nth regulator in the real, alphabetically-sorted /api/documents-derived
// list gets slot N — so a 3rd or 4th regulator being ingested just takes
// the next unused slot with no code change, and nothing is hardcoded to
// "RBI is always j1." Beyond 4 regulators the slots repeat (mod 4) rather
// than erroring — a real scaling limit of the 4-color palette, not a bug.
const SLOT_COUNT = 4;

export function jurisdictionCode(documentName) {
  if (!documentName) return null;
  return documentName.split("_")[0].toUpperCase();
}

export function slotForCode(code, regulators) {
  if (!code || !regulators || regulators.length === 0) return 1;
  const idx = regulators.indexOf(code);
  return (idx >= 0 ? idx % SLOT_COUNT : 0) + 1;
}

export function jurisdictionSlot(documentName, regulators) {
  return slotForCode(jurisdictionCode(documentName), regulators);
}

export function jurisdictionClass(documentName, regulators) {
  return `j${jurisdictionSlot(documentName, regulators)}`;
}

export function classForCode(code, regulators) {
  return `j${slotForCode(code, regulators)}`;
}
