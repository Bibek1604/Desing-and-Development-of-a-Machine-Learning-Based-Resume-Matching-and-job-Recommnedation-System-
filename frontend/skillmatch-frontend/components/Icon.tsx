import {
  BrainCircuit,
  FileSearch,
  MapPin,
  Target,
  ShieldCheck,
  Building2,
  type LucideIcon,
} from "lucide-react";

const icons: Record<string, LucideIcon> = {
  BrainCircuit,
  FileSearch,
  MapPin,
  Target,
  ShieldCheck,
  Building2,
};

export default function Icon({
  name,
  className,
  size = 22,
}: {
  name: string;
  className?: string;
  size?: number;
}) {
  const Cmp = icons[name] ?? BrainCircuit;
  return <Cmp className={className} size={size} aria-hidden />;
}
