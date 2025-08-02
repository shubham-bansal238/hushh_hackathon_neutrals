import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Sidebar,
  SidebarContent,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import {
  Package,
  DollarSign,
  Settings,
  User,
  Clock,
  Shield,
  AlertTriangle,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { updateProductStatus, fetchProducts } from "@/lib/productApi";

interface Product {
  id: number;
  itemname: string;
  purchase_price: number;
  purchase_date: string;
  price_range: string;
  confidence: string;
  status: string;
  reasoning?: string; // Optional reasoning field
}

const Application = () => {
  const navigate = useNavigate();
  const [userEmail, setUserEmail] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:5000/auth/user", { credentials: "include" })
      .then((res) => res.json())
      .then((data) => {
        if (data && data.email) setUserEmail(data.email);
      });
  }, []);

  useEffect(() => {
    fetch("http://localhost:5000/auth/user", { credentials: "include" })
      .then((res) => {
        if (!res.ok) {
          navigate("/");
          return;
        }
        return res.json();
      })
      .then((data) => {
        if (!data || !data.email) {
          navigate("/");
        }
      });
  }, [navigate]);

  useEffect(() => {
    fetchProducts()
      .then((data) => {
        const filtered = data.products.filter((p: Product) => p.status === "resell_candidate");
        setProducts(filtered);
        // Log reasoning for each product
        filtered.forEach((product) => {
          const itemname = product.itemname || "";
          if (product.reasoning) {
            console.log(`Product ID ${product.id} | Item: ${itemname} | Reasoning: ${product.reasoning}`);
          } else {
            console.log(`Product ID ${product.id} | Item: ${itemname} | No reasoning.`);
          }
        });
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleStatusClick = async (product: Product) => {
    let newStatus = "";
    if (product.status === "uncertain") newStatus = "dont_sell";
    else if (product.status === "dont_sell") newStatus = "resell_candidate";
    else if (product.status === "resell_candidate") newStatus = "dont_sell";
    else return;

    try {
      await updateProductStatus(product.id, newStatus);
      fetchProducts().then((data) => {
        setProducts(
          data.products.filter((p: Product) => p.status === "resell_candidate")
        );
      });
    } catch (e) {
      alert("Failed to update status");
    }
  };

  const truncateItemName = (itemname: string) => {
    const words = itemname.split(" ");
    return words.slice(0, 5).join(" ");
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case "resell_candidate":
        return "destructive";
      case "uncertain":
        return "secondary";
      default:
        return "default";
    }
  };

  const getConfidenceIcon = (confidence: string) => {
    switch (confidence) {
      case "high":
        return <Shield className="w-4 h-4 text-green-500" />;
      case "medium":
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case "low":
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen w-screen bg-background flex">
        {/* Sidebar */}
        <Sidebar className="border-r border-sidebar-border bg-sidebar">
          <SidebarContent className="p-4">
            <div className="space-y-6">
              {/* User profile */}
              <div className="text-center">
                <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center mx-auto mb-3 transition-transform hover:scale-105">
                  <User className="w-6 h-6 text-primary-foreground" />
                </div>
                <p className="text-sidebar-foreground text-sm font-medium truncate">
                  {userEmail}
                </p>
              </div>

              {/* Navigation */}
              <nav className="space-y-2">
                <div className="flex items-center space-x-3 p-3 rounded-lg bg-primary text-primary-foreground">
                  
                  <DollarSign className="w-5 h-5" />
                  <span className="font-medium">Resalable items</span>
                </div>

                <div
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-sidebar-accent transition-colors cursor-pointer group"
                  onClick={() => navigate("/resale")}
                >
                  <Package className="w-5 h-5" />
                  <span className="text-sidebar-foreground group-hover:text-sidebar-accent-foreground">
                    All Products
                  </span>
                </div>

                <div
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-sidebar-accent transition-colors cursor-pointer group"
                  onClick={() => navigate("/settings")}
                >
                  <Settings className="w-5 h-5" />
                  <span className="text-sidebar-foreground group-hover:text-sidebar-accent-foreground">
                    Settings
                  </span>
                </div>
              </nav>
            </div>
          </SidebarContent>
        </Sidebar>

        {/* Main content */}
        <div className="flex flex-col min-h-0 flex-1 w-[calc(100%-16rem)]">

          <header className="w-full sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm p-4 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center space-x-4">
              <SidebarTrigger />
              <div>
                <h1 className="text-xl font-semibold text-foreground">
                  Resalable items
                </h1>
                <p className="text-sm text-muted-foreground">
                  {products.length} items need your attention
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={async () => {
                  await fetch("http://localhost:5000/auth/logout", {
                    method: "POST",
                    credentials: "include",
                  });
                  navigate("/");
                }}
              >
                Logout
              </Button>
            </div>
          </header>

          {/* Items grid */}
          <main className="flex-1 p-6 min-h-0 overflow-auto w-full">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : products.length === 0 ? (
              <div className="flex flex-col items-center justify-center w-full h-full text-center">
                <Package className="w-12 h-12 text-muted-foreground/30 mb-4" />
                <h3 className="text-lg font-medium text-muted-foreground mb-2">
                  No items to display
                </h3>
                <p className="text-muted-foreground max-w-md text-sm">
                  Your unused items will appear here once our system analyzes
                  your data.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 w-full">
                {products.map((product) => (
                  <Card
                    key={product.id}
                    className="group hover:shadow-md transition-all duration-200 border-border/50 max-w-[320px] mx-auto"
                  >
                    {/* Card Header */}
                    <div className="p-4 pb-3">
                      <div className="flex items-start justify-between mb-3">
                        <h3 className="font-semibold text-foreground text-lg leading-tight">
                          {product.itemname}
                        </h3>
                        <Badge
                          variant={getStatusVariant(product.status)}
                          className="ml-2 shrink-0 cursor-pointer hover:scale-105 transition-transform"
                          onClick={() => handleStatusClick(product)}
                          title="Click to change status"
                        >
                          {product.status === "resell_candidate"
                            ? "Resell"
                            : product.status.replace("_", " ")}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                        <Clock className="w-4 h-4 text-cyan" />
                        <span>
                          Purchased{" "}
                          {new Date(product.purchase_date).toLocaleDateString()}
                        </span>
                      </div>
                    </div>

                    {/* Price Section */}
                    <div className="px-4 pb-4">
                      <div className="bg-muted/30 rounded-lg p-3 mb-3 space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground uppercase tracking-wide">
                            Purchase Price
                          </span>
                          <span className="text-lg font-bold text-foreground">
                            ₹{product.purchase_price.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground uppercase tracking-wide">
                            Current Range
                          </span>
                          <span className="text-sm font-semibold text-orange">
                            {product.price_range}
                          </span>
                        </div>
                        {/* Reasoning text */}
                        {product.reasoning && (
                          <div className="mt-2 text-xs text-muted-foreground">
                            <span className="font-semibold">Reasoning: </span>{product.reasoning}
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Application;
