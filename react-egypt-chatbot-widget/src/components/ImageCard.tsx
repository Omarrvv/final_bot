import React from "react";

interface ImageCardProps {
  id: string;
  image: string;
  text: string;
  onClick: () => void;
}

const ImageCard: React.FC<ImageCardProps> = ({ image, text, onClick }) => {
  return (
    <div
      onClick={onClick}
      className="relative rounded-2xl overflow-hidden cursor-pointer hover:scale-[1.02] transition-transform shadow-sm"
    >
      <img src={image} alt={text} className="w-full h-48 object-cover" />
      <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
      <div className="absolute bottom-6 left-6 right-6">
        <div className="text-white font-semibold text-base">{text}</div>
      </div>
    </div>
  );
};

export default ImageCard;
