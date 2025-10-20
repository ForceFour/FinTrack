import { Metadata } from "next";
import AnalyticsClient from "./AnalyticsClient";

export const metadata : Metadata = {
  title: "Analytics | Fintrack",
  description: "Detailed financial analytics and insights powered by AI.",
}

export default function AnalyticsPage() {
  return <AnalyticsClient />;
}
