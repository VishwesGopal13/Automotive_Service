import "./globals.css";

export const metadata = {
  title: "AutoService AI",
  description: "AI-powered automotive service system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gradient-to-br from-blue-50 to-indigo-100">
        {children}
      </body>
    </html>
  );
}
