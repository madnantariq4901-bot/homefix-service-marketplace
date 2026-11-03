import type { CategoryName } from "~/types/category"

export interface CategoryMeta {
  label: string
  icon: string
  tagline: string
  examples: string[]
  image: string
}

// Presentation data for each service. The API only stores name / rate / description,
// so icons and example jobs live here. Add a new entry when you add a new CategoryName.
export const categoryMeta: Partial<Record<CategoryName, CategoryMeta>> = {
  plumber: {
    label: "Plumbing",
    icon: "⌁",
    tagline: "Leaks, pipes, drains and fittings",
    examples: ["Leak repair", "Drain unblocking", "Water heater", "Tap and basin fitting"],
    image: "https://images.unsplash.com/photo-1607472586893-edb57bdc0e39?auto=format&fit=crop&w=1200&q=85",
  },
  electrician: {
    label: "Electrical Services",
    icon: "ϟ",
    tagline: "Wiring, lighting and electrical repairs",
    examples: ["Switches and sockets", "Fan and light fitting", "Breaker / fuse faults", "Rewiring"],
    image: "https://images.unsplash.com/photo-1621905251918-48416bd8575a?auto=format&fit=crop&w=1200&q=85",
  },
  carpenter: {
    label: "Carpentry",
    icon: "⌑",
    tagline: "Furniture, doors and custom woodwork",
    examples: ["Door and window repair", "Furniture repair", "Cabinets and shelves", "Custom builds"],
    image: "https://images.unsplash.com/photo-1620626011761-996317b8d101?auto=format&fit=crop&w=1200&q=85",
  },
  mechanic: {
    label: "Mechanic",
    icon: "⚙",
    tagline: "Vehicle diagnostics and repair",
    examples: ["Engine diagnostics", "Oil change", "Battery and tyres", "Brake service"],
    image: "https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?auto=format&fit=crop&w=1200&q=85",
  },
  ac_technician: {
    label: "AC Services",
    icon: "❄",
    tagline: "Air conditioning repair and servicing",
    examples: ["AC installation", "Servicing", "Gas filling", "AC repair"],
    image: "https://images.unsplash.com/photo-1585771724684-38269d6639fd?auto=format&fit=crop&w=1200&q=85",
  },
  painter: {
    label: "Painting",
    icon: "▰",
    tagline: "Interior and exterior painting",
    examples: ["Interior painting", "Exterior painting", "Wall touch-ups", "Wall preparation"],
    image: "https://images.unsplash.com/photo-1562259949-e8e7689d7828?auto=format&fit=crop&w=1200&q=85",
  },
  cleaner: {
    label: "Home Cleaning",
    icon: "✳",
    tagline: "Routine, deep and move-in cleaning",
    examples: ["Home cleaning", "Deep cleaning", "Sofa and carpet cleaning", "Move-in cleaning"],
    image: "https://images.unsplash.com/photo-1581578731548-c64695cc6952?auto=format&fit=crop&w=1200&q=85",
  },
  mason: {
    label: "Mason",
    icon: "▦",
    tagline: "Brickwork, plaster and small repairs",
    examples: ["Brickwork", "Plaster", "Tile and flooring", "Small repairs"],
    image: "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=85",
  },
}

export function getCategoryMeta(name: string): CategoryMeta {
  return (
    categoryMeta[name as CategoryName] ?? {
      label: name.replaceAll("_", " ").replace(/\b\w/g, character => character.toUpperCase()),
      icon: "🛠️",
      tagline: "",
      examples: [],
      image: "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1200&q=85",
    }
  )
}
