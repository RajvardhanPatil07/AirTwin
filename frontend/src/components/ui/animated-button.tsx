import { motion, useReducedMotion, type HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

type AnimatedButtonProps = Omit<HTMLMotionProps<"button">, "children"> & {
  children: ReactNode;
};

export default function AnimatedButton({
  children,
  className,
  ...props
}: AnimatedButtonProps) {
  const reducedMotion = useReducedMotion();
  return (
    <motion.button
      {...props}
      type={props.type ?? "button"}
      className={cn("at-animated-button", className)}
      whileHover={reducedMotion ? undefined : { y: -1 }}
      whileTap={reducedMotion ? undefined : { scale: 0.98 }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
    >
      <span className="at-button-content">{children}</span>
      <span aria-hidden="true" className="at-button-shine" />
    </motion.button>
  );
}
