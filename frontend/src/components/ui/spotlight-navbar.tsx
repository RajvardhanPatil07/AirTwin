import { useRef, useState } from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface NavItem {
  label: string;
  href: string;
}
export interface SpotlightNavbarProps {
  items: NavItem[];
  activeIndex: number;
  onItemClick: (item: NavItem, index: number) => void;
  className?: string;
}

export function SpotlightNavbar({
  items,
  activeIndex,
  onItemClick,
  className,
}: SpotlightNavbarProps) {
  const navRef = useRef<HTMLElement>(null);
  const [hover, setHover] = useState(false);
  return (
    <nav
      ref={navRef}
      className={cn("at-steps", hover && "is-hovered", className)}
      aria-label="Your air quality journey"
      onPointerMove={(event) => {
        const nav = navRef.current;
        if (nav)
          nav.style.setProperty(
            "--spotlight-x",
            `${event.clientX - nav.getBoundingClientRect().left}px`,
          );
        setHover(true);
      }}
      onPointerLeave={() => setHover(false)}
    >
      {items.map((item, index) => (
        <button
          key={item.label}
          className={
            activeIndex === index
              ? "is-current"
              : index < activeIndex
                ? "is-complete"
                : ""
          }
          aria-current={activeIndex === index ? "step" : undefined}
          onClick={() => onItemClick(item, index)}
        >
          <span>{index < activeIndex ? <Check size={12} /> : index + 1}</span>
          {item.label}
        </button>
      ))}
    </nav>
  );
}
