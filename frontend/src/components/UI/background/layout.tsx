import type { ReactNode } from "react";
import { BackgroundPattern } from "./BackgroundPattern";

interface LayoutProps {
  children: ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
  return (
    <div className="relative min-h-screen">
      {/* Background  */}
      <BackgroundPattern />
      
      {/* Page Content */}
      <div className="relative z-10 min-h-screen">
        {children}
      </div>
    </div>
  );
};