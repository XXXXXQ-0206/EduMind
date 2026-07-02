import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function NotFoundPage() {
  return (
    <div className="grid min-h-[60dvh] place-items-center">
      <Card className="max-w-md">
        <CardHeader>
          <CardTitle>页面不存在</CardTitle>
          <CardDescription>该路径没有对应的新 React 页面，可能需要通过兼容重定向访问。</CardDescription>
        </CardHeader>
        <CardContent>
          <Button>
            <Link to="/">回到工作台</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
