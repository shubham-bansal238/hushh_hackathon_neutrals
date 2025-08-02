import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sidebar, SidebarContent, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Package, DollarSign, Settings, User, Clock, Shield, AlertTriangle } from "lucide-react";
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
}

const Application = () => {
  const navigate = useNavigate();
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    fetch("http://localhost:5000/auth/user", { credentials: "include" })
      .then(res => res.json())
      .then(data => {
        if (data && data.email) setUserEmail(data.email);
      });
  }, []);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  // Authentication check on mount
  useEffect(() => {
    fetch("http://localhost:5000/auth/user", { credentials: "include" })
      .then(res => {
        if (!res.ok) {
          navigate("/");
          return;
        }
        return res.json();
      })
      .then(data => {
        if (!data || !data.email) {
          navigate("/");
        }
      });
  }, [navigate]);

  // Fetch products from backend file
  useEffect(() => {
    fetchProducts()
      .then(data => {
        setProducts(data.products.filter((p: Product) => p.status === 'resell_candidate'));
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Status click logic
  const handleStatusClick = async (product: Product) => {
    let newStatus = '';
    if (product.status === 'uncertain') newStatus = 'dont_sell';
    else if (product.status === 'dont_sell') newStatus = 'resell_candidate';
    else if (product.status === 'resell_candidate') newStatus = 'dont_sell';
    else return;
    try {
      await updateProductStatus(product.id, newStatus);
      // Refetch products after update
      fetchProducts()
        .then(data => {
          setProducts(data.products.filter((p: Product) => p.status === 'resell_candidate'));
        });
    } catch (e) {
      alert('Failed to update status');
    }
  };

  const truncateItemName = (itemname: string) => {
    const words = itemname.split(' ');
    return words.slice(0, 5).join(' ');
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'resell_candidate':
        return 'destructive';
      case 'uncertain':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const getConfidenceIcon = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return <Shield className="w-4 h-4 text-green-500" />;
      case 'medium':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'low':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen bg-background flex">
        {/* Sidebar */}
        <Sidebar className="border-r border-sidebar-border bg-sidebar">
          <SidebarContent className="p-6">
            <div className="space-y-8">
              {/* User profile */}
              <div className="text-center">
                <div className="w-12 h-12 bg-sidebar-primary rounded-full flex items-center justify-center mx-auto mb-4">
                  <User className="w-6 h-6 text-sidebar-primary-foreground" />
                </div>
                <p className="text-sidebar-foreground text-sm">{userEmail}</p>
              </div>

              {/* Navigation */}
              <nav className="space-y-2">
                <div className="flex items-center space-x-3 p-3 rounded-lg bg-sidebar-accent text-sidebar-accent-foreground">
                  <Package className="w-5 h-5" />
                  <span className="font-medium">Unused Items</span>
                </div>
                
                <div 
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors cursor-pointer"
                  onClick={() => navigate('/resale')}
                >
                  <DollarSign className="w-5 h-5" />
                  <span>ReSale Value</span>
                </div>
                
                <div 
                  className="flex items-center space-x-3 p-3 rounded-lg hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors cursor-pointer"
                  onClick={() => navigate('/settings')}
                >
                  <Settings className="w-5 h-5" />
                  <span>Settings</span>
                </div>
              </nav>
            </div>
          </SidebarContent>
        </Sidebar>

        {/* Main content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="sticky top-0 z-50 border-b border-border bg-card/95 backdrop-blur-sm p-4 sm:p-6 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <SidebarTrigger />
              <h1 className="text-lg sm:text-2xl font-bold text-foreground">RePrice • Unused Items</h1>
            </div>
            
            <div className="flex items-center space-x-2 sm:space-x-4">
              <div className="hidden sm:block text-sm text-muted-foreground">
                {products.length} items detected
              </div>
              <Button onClick={async () => {
                await fetch("http://localhost:5000/auth/logout", {
                  method: "POST",
                  credentials: "include"
                });
                navigate("/");
              }}>Logout</Button>
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-primary-foreground" />
              </div>
            </div>
          </header>

          {/* Items grid */}
          <main className="flex-1 p-4 sm:p-8 bg-gradient-subtle w-full">
            <div className="mb-8">
              <h2 className="text-3xl font-bold text-foreground mb-2">Uncertain Items</h2>
              <p className="text-muted-foreground">Items that need your attention</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
              {loading ? <div>Loading...</div> : products.map((product, index) => (
                <Card key={product.id} className="group relative overflow-hidden bg-gradient-card border border-border/50 shadow-elegant hover:shadow-glow transition-all duration-500 hover:scale-[1.02] animate-slide-up" style={{animationDelay: `${index * 100}ms`}}>
                  {/* Card Header */}
                  <div className="p-6 pb-4">
                    <div className="flex items-start justify-between mb-4">
                      <h3 className="font-bold text-foreground text-xl leading-tight">
                        {truncateItemName(product.itemname)}
                      </h3>
                      <Badge 
                        variant={getStatusVariant(product.status)} 
                        className="ml-2 shrink-0 cursor-pointer"
                        onClick={() => handleStatusClick(product)}
                        title="Click to change status"
                      >
                        {product.status.replace('_', ' ')}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
                      <Clock className="w-4 h-4" />
                      <span>Purchased on {new Date(product.purchase_date).toLocaleDateString()}</span>
                    </div>
                  </div>
                  {/* Price Section */}
                  <div className="px-6 pb-6">
                    <div className="bg-muted/30 rounded-xl p-4 mb-4">
                      <div className="grid grid-cols-1 gap-4">
                        <div>
                          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Purchase Price</p>
                          <p className="text-lg font-bold text-foreground">₹{product.purchase_price.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Current Range</p>
                          <p className="text-lg font-bold text-foreground">{product.price_range}</p>
                        </div>
                      </div>
                    </div>
                    {/* Action Button */}
                    <Button 
                      className="w-full bg-gradient-primary hover:opacity-90 text-white font-semibold rounded-xl h-11 transition-all duration-300 hover:shadow-glow group-hover:scale-[1.02]"
                    >
                      List for Resale
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Application;