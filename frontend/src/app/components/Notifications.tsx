import { useState } from "react";
import { Bell, Clock, CheckCircle, AlertCircle, Info } from "lucide-react";
import { toast } from "sonner";

const initialNotifications = [
  {
    id: 1,
    title: "Miami GP Ready for Analysis",
    description: "AI model is ready to generate predictions for the Miami Grand Prix. Adjust factors and run the model!",
    time: "2 hours ago",
    unread: true,
    type: "info",
  },
  {
    id: 2,
    title: "AI Prediction Was Correct!",
    description: "Congratulations! The AI model accurately predicted the China GP podium. You earned 68 points.",
    time: "1 day ago",
    unread: true,
    type: "success",
  },
  {
    id: 3,
    title: "New Season Starting Soon",
    description: "The 2026 F1 season is about to begin in 3 days. Get ready to see AI predictions!",
    time: "2 days ago",
    unread: false,
    type: "info",
  },
  {
    id: 4,
    title: "Race Starting Soon",
    description: "Japan GP starts in 2 hours. Generate your AI prediction before the race begins!",
    time: "3 days ago",
    unread: false,
    type: "warning",
  },
  {
    id: 5,
    title: "Model on a Winning Streak!",
    description: "Amazing! The AI model has correctly predicted 5 races in a row with your factor settings!",
    time: "4 days ago",
    unread: false,
    type: "success",
  },
  {
    id: 6,
    title: "Race Results Updated",
    description: "The official results for Australia GP have been posted. Check the AI model's accuracy.",
    time: "5 days ago",
    unread: false,
    type: "info",
  },
];

export default function Notifications() {
  const [notifications, setNotifications] = useState(initialNotifications);

  const getIcon = (type: string) => {
    switch (type) {
      case "success":
        return <CheckCircle className="h-5 w-5 text-[#00ff88]" />;
      case "warning":
        return <AlertCircle className="h-5 w-5 text-[#ffd700]" />;
      default:
        return <Info className="h-5 w-5 text-[#00d4ff]" />;
    }
  };

  const markAllAsRead = () => {
    setNotifications((prev) =>
      prev.map((notification) => ({ ...notification, unread: false }))
    );
    toast.success("All notifications marked as read");
  };

  const markAsRead = (id: number) => {
    setNotifications((prev) =>
      prev.map((notification) =>
        notification.id === id ? { ...notification, unread: false } : notification
      )
    );
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto max-w-4xl px-6">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="mb-2 text-4xl font-bold tracking-tight text-foreground">
              Notifications
            </h1>
            <p className="text-muted-foreground">
              Stay updated with your predictions and race alerts
            </p>
          </div>
          <button
            onClick={markAllAsRead}
            className="rounded-lg bg-secondary px-4 py-2 text-sm text-foreground transition-all hover:bg-secondary/80"
          >
            Mark All as Read
          </button>
        </div>

        <div className="space-y-4">
          {notifications.map((notification) => (
            <button
              key={notification.id}
              onClick={() => markAsRead(notification.id)}
              className={`w-full overflow-hidden rounded-2xl border text-left transition-all hover:shadow-lg ${
                notification.unread
                  ? "border-[#e10600]/30 bg-gradient-to-br from-[#e10600]/10 to-card/80"
                  : "border-border bg-gradient-to-br from-card/80 to-secondary/40"
              } backdrop-blur-xl`}
            >
              <div className="p-6">
                <div className="flex gap-4">
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-secondary/50">
                    {getIcon(notification.type)}
                  </div>
                  <div className="flex-1">
                    <div className="mb-1 flex items-start justify-between gap-4">
                      <h3 className="font-semibold text-foreground">
                        {notification.title}
                      </h3>
                      {notification.unread && (
                        <span className="flex-shrink-0 rounded-full bg-[#e10600] px-2 py-0.5 text-xs text-white">
                          New
                        </span>
                      )}
                    </div>
                    <p className="mb-3 text-sm text-muted-foreground">
                      {notification.description}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      <span>{notification.time}</span>
                    </div>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>

        {notifications.length === 0 && (
          <div className="rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-12 text-center backdrop-blur-xl">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-secondary/50">
              <Bell className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="mb-2 text-lg font-semibold text-foreground">No notifications</h3>
            <p className="text-sm text-muted-foreground">
              You're all caught up! We'll notify you when something important happens.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
