import React, { useRef, useCallback, useState, useEffect } from "react";
import Webcam from "react-webcam";
import axios from "axios";

const FaceVerification = () => {

    const webcamRef = useRef(null);
    const [user, setUser] = useState("");

    const capture = useCallback(async () => {
        const imageSrc = webcamRef.current.getScreenshot();
        if (!imageSrc) return;

        const blob = await fetch(imageSrc).then((res) => res.blob());
        const formData = new FormData();
        formData.append("file", blob, "frame.jpg");

        try {
            const response = await axios.post("http://localhost:8000/verify", formData);
            if (response.data.faces?.length > 0) {
                setUser(response.data.faces[0].name);
            } else {
                setUser("");
            }
        } catch (error) {
            console.error("Error verifying face:", error);
        }
    }, []);

    useEffect(() => {
        const interval = setInterval(() => {
            capture();
        }, 2000);
        return () => clearInterval(interval);
    }, [capture, user]);

    const hour = new Date().getHours();

    console.log(user)

    const getGreeting = () => {
        if (hour < 4) return "Good night";
        if (hour < 12) return "Good morning";
        if (hour < 16) return "Good afternoon";
        if (hour < 21) return "Good evening";
        return "Good night";
    };

    return (
        <div className="w-3/4 m-auto text-center">
            <Webcam
                audio={false}
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                width={480}
                className="m-auto rotate-y-180"
            />
            {user &&
                <h2 className="font-bold text-2xl" >{getGreeting()} {user}</h2>
            }
        </div>
    )
}

export default FaceVerification
