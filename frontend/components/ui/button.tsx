import * as React from "react";
import { cn } from "@/lib/utils";

const Button = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ className, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center rounded-full bg-black text-white",
        "h-9 w-9 shrink-0 transition-opacity hover:opacity-80",
        "disabled:pointer-events-none disabled:opacity-30",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black",
        className
      )}
      {...props}
    />
  )
);
Button.displayName = "Button";

export { Button };
