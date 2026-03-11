const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const client = new Client({
    authStrategy: new LocalAuth()
});

client.on('qr', (qr) => {
    // Generate and scan this code with your phone
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('WhatsApp Agent is live');
});

client.on('message', async msg => {
    try {
        if (!msg.body || msg.body.trim() === "") return;
        if (msg.fromMe) return;

        let senderName = "Unknown";
        try {
            const contact = await msg.getContact();
            senderName = contact.pushname || contact.name || contact.number || "Unknown";
        } catch(e) {
            console.log("Could not get contact name, skipping message");
            return;
        }

        if (!senderName) return;
        const sender_number = msg.from;
        const message_text = msg.body;
        const is_group = msg.from.includes('@g.us');

        let groupName = "";
        if (is_group) {
            const chat = await msg.getChat();
            groupName = chat.name;
        }

        const payload = {
            sender_name: senderName,
            sender_number: sender_number,
            message: message_text,
            is_group: is_group,
            group_name: groupName
        };

        const response = await axios.post('http://localhost:8000/reply', payload);

        if (response.data && response.data.reply) {
            const delay_ms = response.data.delay_ms || 2000;
            
            setTimeout(async () => {
                try {
                    await msg.reply(response.data.reply);
                } catch (replyError) {
                    console.error("Error sending reply:", replyError);
                }
            }, delay_ms);
        }

    } catch (error) {
        console.error("Error processing message:", error);
    }
});

client.initialize();
