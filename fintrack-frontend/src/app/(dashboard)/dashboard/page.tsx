import { Metadata } from "next";
import DashboardClient from "./DashboardClient";

export const metadata : Metadata = {
  title: "Dashboard | Fintrack",
  description: "Your financial dashboard powered by AI.",
}

export default function DashboardPage() {
  return <DashboardClient />;
}
