import { useState, useEffect, useCallback, createContext, useContext, type ReactNode } from "react";

interface ToastMessage {
  id: number;
  text: string;
  type: "success" | "error" | "info";
}

interface ToastContextType {
  toast: (text: string, type?: ToastMessage["type"]) => void;
}

const ToastContext = createContext<ToastContextType>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ToastMessage[]>([]);

  const toast = useCallback((text: string, type: ToastMessage["type"] = "info") => {
    const id = nextId++;
    setMessages((prev) => [...prev, { id, text, type }]);
  }, []);

  const remove = useCallback((id: number) => {
    setMessages((prev) => prev.filter((m) => m.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {messages.map((m) => (
          <ToastItem key={m.id} message={m} onDismiss={() => remove(m.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function ToastItem({ message, onDismiss }: { message: ToastMessage; onDismiss: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 4000);
    return () => clearTimeout(t);
  }, [onDismiss]);

  const colors = {
    success: "bg-green-600",
    error: "bg-red-600",
    info: "bg-gray-800 dark:bg-gray-700",
  };

  return (
    <div
      className={`${colors[message.type]} text-white px-4 py-3 rounded-lg shadow-lg text-sm max-w-sm animate-slide-in cursor-pointer`}
      onClick={onDismiss}
    >
      {message.text}
    </div>
  );
}
