import React from "react";
import { Moon, Sun } from "lucide-react";
import { appSections, canShowSection, getInitialSection, navGroups, shouldRedirectSection, type AppSection, type PrinterAvailability } from "../../app/navigation";
import type { ThemeMode } from "../../types";

export function useAppShell(
  printerAvailability: PrinterAvailability,
  isPlatformAdmin: boolean | null,
) {
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
    if (shouldRedirectSection(activeSection, printerAvailability)) {
      setActiveSection("printer-detail");
    }
  }, [activeSection, printerAvailability]);

  React.useEffect(() => {
    if (activeSection === "design-system" && isPlatformAdmin === false) {
      setActiveSection("overview");
    }
  }, [activeSection, isPlatformAdmin]);

  const activeSectionMeta = appSections.find((section) => section.key === activeSection) ?? appSections[0];
  const ActiveIcon = activeSectionMeta.icon;
  const ThemeIcon = theme === "dark" ? Sun : Moon;
  const visibleNavGroups = React.useMemo(
    () =>
      navGroups
        .map((group) => ({
          ...group,
          sections: group.sections.filter((sectionKey) =>
            canShowSection(sectionKey, printerAvailability, isPlatformAdmin === true)
          ),
        }))
        .filter((group) => group.sections.length > 0),
    [isPlatformAdmin, printerAvailability],
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
