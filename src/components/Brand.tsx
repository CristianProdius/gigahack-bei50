import Image from "next/image";

export default function Brand() {
  return (
    <div className="brand flex items-center gap-3">
      <Image className="brand-mark" src="/brand/trashopoly-mark.png" alt="" aria-hidden="true" width={48} height={42} loading="eager" unoptimized />
      <span>TRASHOPOLY</span>
    </div>
  );
}
