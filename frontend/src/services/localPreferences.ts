export type DocumentTheme = "light" | "dark";

const THEME_KEY = "printora-theme";
const SETUP_RECIPE_KEY = "printora.setup.recipe.v1";

export function readDocumentTheme(): DocumentTheme {
  return window.localStorage.getItem(THEME_KEY) === "light" ? "light" : "dark";
}

export function readSetupRecipe<T extends Record<string, boolean>>(): Partial<T> | null {
  const saved = window.localStorage.getItem(SETUP_RECIPE_KEY);
  if (!saved) return null;
  try {
    return JSON.parse(saved) as Partial<T>;
  } catch {
    window.localStorage.removeItem(SETUP_RECIPE_KEY);
    return null;
  }
}

export function writeSetupRecipe<T extends Record<string, boolean>>(value: T): void {
  window.localStorage.setItem(SETUP_RECIPE_KEY, JSON.stringify(value));
}
