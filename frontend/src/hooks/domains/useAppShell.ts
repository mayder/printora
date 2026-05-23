import React from "react";
import { Moon, Sun } from "lucide-react";
import { appSections, getInitialSection, navGroups, onlinePrinterSections, selectedPrinterLocalSections, type AppSection } from "../../app/navigation";
import type { ThemeMode } from "../../types";

export function useAppShell(selectedPrinterId: number | null) {
  const [activeSection, setActiveSection] = React.useState<AppSection>(() => getInitialSection());
  const [theme, setTheme] = React.useState<ThemeMode>(() => {
    const storedTheme = window.localStorage.getItem("printora-theme");
    return storedTheme === "light" ? "light" : "dark";
  });
  const [alertCenterOpen, setAlertCenterOpen] = React.useState(false);
  const [mobileNavOpen, setMobileNavOpen] = React.useState(false);

  React.useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("printora-theme", theme);
  }, [theme]);

  React.useEffect(() => {
    if (onlinePrinterSections.has(activeSection) && !selectedPrinterId) {
      setActiveSection("overview");
      return;
    }
    if (selectedPrinterLocalSections.has(activeSection) && !selectedPrinterId) {
      setActiveSection("overview");
    }
  }, [activeSection, selectedPrinterId]);

  const activeSectionMeta = appSections.find((section) => section.key === activeSection) ?? appSections[0];
  const ActiveIcon = activeSectionMeta.icon;
  const ThemeIcon = theme === "dark" ? Sun : Moon;
  const visibleNavGroups = React.useMemo(
    () =>
      navGroups
        .map((group) => ({
          ...group,
          sections: group.sections.filter((sectionKey) => {
            if (onlinePrinterSections.has(sectionKey)) {
              return Boolean(selectedPrinterId);
            }
            if (selectedPrinterLocalSections.has(sectionKey)) {
              return Boolean(selectedPrinterId);
            }
            return true;
          }),
        }))
        .filter((group) => group.sections.length > 0),
    [selectedPrinterId],
  );

  return {
    ActiveIcon,
    ThemeIcon,
    activeSection,
    activeSectionMeta,
    alertCenterOpen,
    mobileNavOpen,
    setActiveSection,
    setAlertCenterOpen,
    setMobileNavOpen,
    setTheme,
    theme,
    visibleNavGroups,
  };
}
