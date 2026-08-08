import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { CampaignsPage } from "@/pages/Campaigns";
import { CompanyDetailsPage } from "@/pages/CompanyDetails";
import { CrawlerMonitorPage } from "@/pages/CrawlerMonitor";
import { DashboardPage } from "@/pages/Dashboard";
import { DiscoverPage } from "@/pages/Discover";
import { ListsPage } from "@/pages/Lists";
import { SearchPage } from "@/pages/Search";
import { SettingsPage } from "@/pages/Settings";

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/discover" element={<DiscoverPage />} />
        <Route path="/campaigns" element={<CampaignsPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/lists" element={<ListsPage />} />
        <Route path="/companies/:id" element={<CompanyDetailsPage />} />
        <Route path="/crawlers" element={<CrawlerMonitorPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
