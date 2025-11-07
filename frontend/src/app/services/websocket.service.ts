import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { environment } from '../../environments/environment';
import { Packet } from '../models/packet.model';

@Injectable({
  providedIn: 'root'
})
export class WebsocketService {
  private socket?: WebSocket;
  private packetSubject = new Subject<Packet>();
  private connectedSubject = new Subject<boolean>();

  public packets$: Observable<Packet> = this.packetSubject.asObservable();
  public connected$: Observable<boolean> = this.connectedSubject.asObservable();

  constructor() {
    this.connect();
  }

  private connect(): void {
    try {
      this.socket = new WebSocket(environment.wsUrl);

      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.connectedSubject.next(true);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'packet') {
            this.packetSubject.next(data.data);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.connectedSubject.next(false);
      };

      this.socket.onclose = () => {
        console.log('WebSocket disconnected. Reconnecting in 5 seconds...');
        this.connectedSubject.next(false);
        setTimeout(() => this.connect(), 5000);
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      setTimeout(() => this.connect(), 5000);
    }
  }

  public disconnect(): void {
    if (this.socket) {
      this.socket.close();
    }
  }
}
