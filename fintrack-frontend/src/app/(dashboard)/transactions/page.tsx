import { Metadata } from "next";
import TransactionsPage from "./TransactionClient";

export const metadata : Metadata = {
    title: "Transactions | Fintrack",
    description: "Manage and view your financial transactions powered by AI.",
}

export default function TransactionsPageWrapper() {
    return <TransactionsPage />;
}
