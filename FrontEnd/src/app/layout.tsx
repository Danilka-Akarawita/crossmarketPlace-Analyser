import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Laptop Intelligence Chat",
  description: "Shopping assistant powered by CrossmarketPlace Analyzer",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
