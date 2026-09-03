import { Button as ButtonPrimitive } from "@base-ui/react/button";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex shrink-0 cursor-pointer items-center justify-center rounded-none border-2 bg-transparent px-4 py-[11px] font-display text-[11px] font-normal tracking-[0.1em] whitespace-nowrap uppercase transition-colors duration-[120ms] ease-out select-none outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-rust disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "border-rust bg-rust text-paper hover:border-petroleum hover:bg-petroleum hover:text-paper",
        outline:
          "border-petroleum bg-transparent text-petroleum hover:bg-fromage hover:text-petroleum",
        secondary:
          "border-petroleum bg-transparent text-petroleum hover:bg-fromage hover:text-petroleum",
        ghost: "border-transparent text-petroleum hover:bg-fromage",
        destructive:
          "border-petroleum/40 text-petroleum/75 hover:border-petroleum hover:bg-sand",
        link: "border-transparent px-0 py-0 text-rust hover:text-petroleum hover:underline",
      },
      size: {
        default: "",
        xs: "px-2 py-1.5 text-[10px]",
        sm: "px-3 py-2 text-[10px]",
        lg: "px-4 py-[13px]",
        icon: "size-8 p-0",
        "icon-xs": "size-6 p-0",
        "icon-sm": "size-7 p-0",
        "icon-lg": "size-9 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: ButtonPrimitive.Props & VariantProps<typeof buttonVariants>) {
  return (
    <ButtonPrimitive
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };
