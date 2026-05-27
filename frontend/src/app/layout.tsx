import type { Metadata } from "next"
import { Geist } from "next/font/google"
import "./globals.css"
import { Providers } from "@/components/Providers"

const geist = Geist({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "MangáPanel",
  description: "Painel de gestão de mangás, manhwas e novels",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR" className="dark">
      <body className={geist.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}