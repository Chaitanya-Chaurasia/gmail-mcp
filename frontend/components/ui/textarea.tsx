import * as React from "react";
import { cn } from "@/lib/utils";

const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea
    ref={ref}
    className={cn(
      "flex w-full resize-none rounded-3xl border border-neutral-300 bg-white",
      "px-4 py-2.5 text-[15px] leading-5 text-black placeholder:text-neutral-400",
      "focus-visible:outline-none focus-visible:border-black",
      "disabled:opacity-50",
      className
    )}
    {...props}
  />
));
Textarea.displayName = "Textarea";

export { Textarea };
