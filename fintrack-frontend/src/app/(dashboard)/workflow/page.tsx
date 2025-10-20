import { Metadata } from "next";
import WorkflowPage from "./WorkflowClient";


export const metadata : Metadata = {
    title: "Workflow | Fintrack",
    description: "Manage and automate your financial workflows powered by AI.",
}

export default function WorkflowPageWrapper() {
    return <WorkflowPage />;
}
