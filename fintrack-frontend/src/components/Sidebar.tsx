"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApp } from "@/app/providers";
import {
  HomeIcon,
  ArrowUpTrayIcon,
  ChartBarIcon,
  LightBulbIcon,
  TagIcon,
  ShieldCheckIcon,
  CogIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
} from "@heroicons/react/24/outline";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: HomeIcon },
  { name: "Upload Transactions", href: "/upload", icon: ArrowUpTrayIcon },
  { name: "Agent Workflow", href: "/workflow", icon: CogIcon },
  { name: "Analytics", href: "/analytics", icon: ChartBarIcon },
  { name: "Suggestions", href: "/suggestions", icon: LightBulbIcon },
  { name: "Categories", href: "/categories", icon: TagIcon },
  { name: "Security", href: "/security", icon: ShieldCheckIcon },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { auth, logout } = useApp();

  return (
    <div className="flex flex-col w-64 bg-gray-900 text-white h-screen">
      <div className="flex items-center justify-center h-16 bg-gray-800">
        <h1 className="text-2xl font-bold">🤖 FinTrack</h1>
      </div>

      <div className="flex flex-col flex-1 overflow-y-auto">
        <nav className="flex-1 px-2 py-4 space-y-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors ${
                  isActive
                    ? "bg-gray-800 text-white"
                    : "text-gray-300 hover:bg-gray-800 hover:text-white"
                }`}
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="px-2 py-4 border-t border-gray-700">
          {auth.user && (
            <div className="flex items-center px-4 py-2 mb-2">
              <UserCircleIcon className="w-8 h-8 mr-3 text-gray-400" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {auth.user.full_name}
                </p>
                <p className="text-xs text-gray-400 truncate">
                  {auth.user.email}
                </p>
              </div>
            </div>
          )}
          <button
            onClick={logout}
            className="flex items-center w-full px-4 py-3 text-sm font-medium text-gray-300 rounded-md hover:bg-gray-800 hover:text-white transition-colors"
          >
            <ArrowRightOnRectangleIcon className="w-5 h-5 mr-3" />
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}
