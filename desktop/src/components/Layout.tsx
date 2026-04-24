import { ReactNode, useState, createContext, useContext } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

interface SidebarCtx {
  open: boolean;
  toggle: () => void;
  close: () => void;
}

const SidebarContext = createContext<SidebarCtx>({
  open: true,
  toggle: () => {},
  close: () => {},
});

export function useSidebar() {
  return useContext(SidebarContext);
}

export function Layout({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(true);

  const ctx: SidebarCtx = {
    open,
    toggle: () => setOpen((o) => !o),
    close: () => setOpen(false),
  };

  return (
    <SidebarContext.Provider value={ctx}>
      <div className="h-screen w-screen bg-carbon-950 text-carbon-100 flex overflow-hidden">
        {/* Sidebar — collapses to w-0 when closed */}
        <div
          className={`shrink-0 transition-[width] duration-200 overflow-hidden ${
            open ? "w-60" : "w-0"
          }`}
        >
          <Sidebar />
        </div>

        {/* Mobile overlay */}
        {open && (
          <div
            className="fixed inset-0 z-10 bg-carbon-950/70 backdrop-blur-sm lg:hidden"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
        )}

        <div className="flex-1 flex flex-col overflow-hidden min-w-0">
          <TopBar />
          <main className="flex-1 overflow-y-auto p-4 md:p-6" id="main-content">
            {children}
          </main>
        </div>
      </div>
    </SidebarContext.Provider>
  );
}
