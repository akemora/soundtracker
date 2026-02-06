import { render, screen } from "@testing-library/react";
import {
  Card,
  CardHeader,
  CardContent,
  CardFooter,
  CardTitle,
  CardDescription,
  CardAction,
} from "@/components/ui/card";
import { Button, buttonVariants } from "@/components/ui/button";
import { Badge, badgeVariants } from "@/components/ui/badge";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogHeader,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Pagination } from "@/components/ui/Pagination";
import Link from "next/link";

describe("ui components", () => {
  it("renders Button and Badge", () => {
    render(
      <div>
        <Button data-testid="btn">Click</Button>
        <Button data-testid="btn-outline" variant="outline" size="icon">
          O
        </Button>
        <Button asChild>
          <Link href="/link">Link</Link>
        </Button>
        <Badge data-testid="badge">New</Badge>
        <Badge data-testid="badge-outline" variant="outline">
          Outline
        </Badge>
        <Badge asChild>
          <Link href="/badge">B</Link>
        </Badge>
      </div>
    );
    expect(screen.getByTestId("btn")).toHaveAttribute("data-variant", "default");
    expect(screen.getByTestId("btn-outline")).toHaveAttribute("data-size", "icon");
    expect(screen.getByTestId("badge")).toHaveAttribute("data-slot", "badge");
    expect(screen.getByTestId("badge-outline")).toHaveAttribute("data-variant", "outline");
    expect(screen.getByText("Link")).toHaveAttribute("href", "/link");
    expect(badgeVariants({ variant: "link" })).toContain("underline");
    expect(buttonVariants({ variant: "ghost", size: "xs" })).toContain("hover:bg-accent");
  });

  it("renders Card parts", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Title</CardTitle>
          <CardDescription>Desc</CardDescription>
          <CardAction>Act</CardAction>
        </CardHeader>
        <CardContent>Content</CardContent>
        <CardFooter>Footer</CardFooter>
      </Card>
    );
    expect(screen.getByText("Content")).toHaveAttribute("data-slot", "card-content");
  });

  it("renders Dialog pieces", () => {
    render(
      <Dialog open>
        <DialogTrigger>Open</DialogTrigger>
        <DialogPortal>
          <DialogOverlay />
        </DialogPortal>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Dialog Title</DialogTitle>
          </DialogHeader>
          <DialogDescription>Dialog Desc</DialogDescription>
          <DialogFooter showCloseButton>
            <button>Action</button>
          </DialogFooter>
          <DialogClose>Close</DialogClose>
        </DialogContent>
      </Dialog>
    );
    expect(screen.getByText("Dialog Title")).toBeInTheDocument();
    expect(screen.getAllByText("Close").length).toBeGreaterThan(0);
  });

  it("renders DialogFooter without close button", () => {
    render(
      <Dialog open>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Footer Dialog</DialogTitle>
          </DialogHeader>
          <DialogDescription>Footer dialog description</DialogDescription>
          <DialogFooter>
            <button>Action</button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
    expect(screen.getByText("Action")).toBeInTheDocument();
  });

  it("renders Input, Separator, Skeleton", () => {
    const { container } = render(
      <div>
        <Input type="text" defaultValue="x" />
        <Separator orientation="vertical" />
        <Skeleton />
      </div>
    );
    expect(screen.getByDisplayValue("x")).toHaveAttribute("data-slot", "input");
    expect(container.querySelector('[data-slot="separator"]')).toBeInTheDocument();
    expect(container.querySelector('[data-slot="skeleton"]')).toBeInTheDocument();
  });

  it("renders Pagination with separators", () => {
    const { rerender } = render(
      <Pagination currentPage={1} totalPages={3} baseUrl="/composers" />
    );
    expect(screen.getByText("← Anterior")).toBeInTheDocument();
    expect(screen.getByText("Siguiente →")).toBeInTheDocument();

    rerender(<Pagination currentPage={2} totalPages={5} baseUrl="/composers?sort=name" />);
    expect(screen.getByText("2 / 5")).toBeInTheDocument();

    rerender(<Pagination currentPage={10} totalPages={20} baseUrl="/composers" />);
    expect(screen.getAllByText("...").length).toBeGreaterThan(1);

    rerender(<Pagination currentPage={6} totalPages={12} baseUrl="/composers" />);
    expect(screen.getAllByText("...")).toHaveLength(2);

    rerender(<Pagination currentPage={4} totalPages={7} baseUrl="/composers" />);
    expect(screen.queryByText("...")).not.toBeInTheDocument();
  });
});
