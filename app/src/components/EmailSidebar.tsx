import { useEffect, useState } from "react";

interface EmailSidebarProps {
  onEmailSelect: (emailId: string) => void;
  selectedEmailId?: string;
}

export function EmailSidebar({ onEmailSelect, selectedEmailId }: EmailSidebarProps) {
  const [emailIds, setEmailIds] = useState<string[]>([]);

  useEffect(() => {
    const fetchEmailIds = async () => {
      const userEmail = sessionStorage.getItem("user_email");
      if (!userEmail) return;

      try {
        const response = await fetch(`/api/firestore/emails/${userEmail}`);
        if (!response.ok) {
          throw new Error("Failed to fetch email IDs");
        }
        const data = await response.json();
        setEmailIds(data);
      } catch (error) {
        console.error("Error fetching email IDs:", error);
      }
    };

    fetchEmailIds();
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-lg font-bold mb-4">Emails</h2>
      <ul className="space-y-2">
        {emailIds.map((emailId) => (
          <li
            key={emailId}
            className={`p-2 cursor-pointer rounded ${
              selectedEmailId === emailId ? "bg-blue-500 text-white" : "bg-gray-100"
            }`}
            onClick={() => onEmailSelect(emailId)}
          >
            {emailId}
          </li>
        ))}
      </ul>
    </div>
  );
}
