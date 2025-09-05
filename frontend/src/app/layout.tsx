import type { Metadata } from "next";
import { Lora, Montserrat } from "next/font/google";
import "./globals.css";
import { Layout } from "@/components/UI/background/layout";
import { Providers } from "@/components/Redux/Provider";

//font family 
const montserrat = Montserrat({
  variable: "--font-montserrat",
  subsets: ["latin"],
});

const lora = Lora({
  subsets: ["latin"],
  variable: "--font-lora",
});


// meta tag 
export const metadata: Metadata = {
  title: "Home Page",
  description: "search kid home page ",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {


  return (
    <html lang="en">
      <body
        className={`${montserrat.variable} ${lora.variable} antialiased`}
      >
        <Providers>
          <Layout>
            {children}
          </Layout>
        </Providers>
      </body>
    </html>
  );
}
